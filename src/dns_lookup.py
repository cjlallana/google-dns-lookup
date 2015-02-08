'''
Created on Jan 20, 2015

@author: Carlos Lallana
@version: 1.0

Useful links:

- Needed DNS lookup library:
http://www.dnspython.org/

- Static IP Addresses and App Engine apps:
https://cloud.google.com/appengine/kb/general#static-ip
'''

import os
#import logging

import sys
# dns.py inside 'libs' folder, inside 'src'
sys.path.insert(0, 'libs')

from dns import resolver

import jinja2
import webapp2



# Not doing anything yet, just there for further development
class View():
	
	def renderHtml(self, request, template_data):
		template = JINJA_ENVIRONMENT.get_template('templates/dns_lookup.html')
		request.response.write(template.render(template_data))


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
					all_ips_info = txt_data.to_text()
					all_ips_info = all_ips_info.replace('"v=spf1 ', '').replace('ip4:', '').replace(' ?all"','')
					ips_list = all_ips_info.split()
					for ip in ips_list:
						ip_ranges.append(ip)

			
			# SORTING IP ADDRESSES 
			#(http://www.secnetix.de/olli/Python/tricks.hawk#sortips)
			for i in range(len(ip_ranges)):
				ip_ranges[i] = "%3s.%3s.%3s.%3s" % tuple(ip_ranges[i].split("."))
			ip_ranges.sort()
			
			for i in range(len(ip_ranges)):
				ip_ranges[i] = ip_ranges[i].replace(" ", "")
			
			# Format the response
			html_response = '<h1>Google IP Ranges</h1>'
			html_response += '<h2>Resolved from _cloud-netblocks.googleusercontent.com</h2>'
			
			for i in ip_ranges:
				html_response += '%s<br>' % (i)
				
			html_response += '<h3>IPs separated by comma (if useful):</h3>'
			for i in ip_ranges:
				html_response += '%s, ' % (i)
				
			html_response += '<br><h3>Check the code <a href="https://github.com/cjlallana/google-dns-lookup">here</a></h3>'
			
			self.response.out.write(html_response)


JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

app = 	webapp2.WSGIApplication([
			('/', Controller), 
		], debug=True)
