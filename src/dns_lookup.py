'''
Created on 2015/01/20
Updated on 2019/11/06

@author: Carlos Lallana
@version: 1.5

Useful links:

- Needed DNS lookup library:
http://www.dnspython.org/

- Static IP Addresses and App Engine apps:
https://cloud.google.com/appengine/kb/general#static-ip
'''
import logging

import webapp2
from dns import resolver
from ipaddress import ip_network


class Controller(webapp2.RequestHandler):

	def get(self):
		
		# Create a new instance of Resolver
		r = resolver.Resolver()
		# Set the server address (Google public DNS)
		r.nameservers = ['8.8.8.8', '8.8.4.4']
		# Execute the query to get the resolver answer. The response will be
		# of type 'TXT'
		r_answer = r.query('_cloud-netblocks.googleusercontent.com', 'TXT')

		# For each TXT record (which is only one)...		
		for txt_data in r_answer:

			# Convert it to text to get the full netblocks info
			all_netblocks_info = txt_data.to_text()
			logging.info(all_netblocks_info)
			# Replace all the extra info to get just the cloud-netblocks entries
			all_netblocks_info = all_netblocks_info.replace('"v=spf1 ', '').replace('include:', '').replace(' ?all"','')
			# Put them into a list
			netblocks_list = all_netblocks_info.split()
			
			ip_ranges = []

			# For each new cloud-netblock...
			for netblock in netblocks_list:
				# Query again to find the netblock's IP ranges
				r_answer = r.query(netblock, 'TXT')
				
				# Same proccess as before, this time getting IPs
				for txt_data in r_answer:
					txt_data_str = txt_data.to_text()
					# Remove the 'ip4' part from each entry, to better identify
					# IPs later
					txt_data_str = txt_data_str.replace('ip4:', '').replace('ip6', '')
					values_list = txt_data_str.split()

					# IP validation: check if any of the values on each TXT
					# entry (which contains all the SPF configs) is a valid IP
					for value in values_list:
						if is_valid_ip(value): ip_ranges.append(value)

			# SORTING IP ADDRESSES 
			#(http://www.secnetix.de/olli/Python/tricks.hawk#sortips)
			for i in range(len(ip_ranges)):
				ip_ranges[i] = "%3s.%3s.%3s.%3s" % tuple(ip_ranges[i].split("."))
			ip_ranges.sort()
			
			for i in range(len(ip_ranges)):
				ip_ranges[i] = ip_ranges[i].replace(" ", "")
			
			# Format the response
			html_response = '<h1>Google Cloud outgoing IP ranges</h1>'
			html_response += ('<h2>Resolved as suggested in the ' +
							'<a href="https://cloud.google.com/appengine/kb/#static-ip">docs</a></h2>')
			
			for i in ip_ranges:
				html_response += '%s<br>' % (i)
				
			html_response += '<h3>List of the above IPs separated by comma (if useful):</h3>'
			for i in ip_ranges:
				html_response += '%s, ' % (i)
				
			html_response += ('<br><h3>Source code ' +
							'<a href="https://github.com/cjlallana/google-dns-lookup">here</a>!</h3>')
			
			self.response.out.write(html_response)


def is_valid_ip(ip_str):

	ip_unicode = ip_str.decode('unicode-escape')

	try:
		ip_network(ip_unicode)
		return True

	except:
		logging.info('Not a valid IP: %s' % ip_unicode)
		return False


app = webapp2.WSGIApplication([
		('/', Controller), 
	], debug=True)
