import time
from marionette_driver.marionette import Marionette

print("Connecting to Marionette server...")
client = Marionette('localhost', port=3838)
print("Connected to Marionette server.")

# Wait a few seconds to let Firefox finish starting up
time.sleep(5)
print("Starting Marionette session...")
client.start_session()
print("Started Marionette session.")

# Execute JavaScript to get the current DOM
print("Executing JavaScript to get the current DOM...")
dom = client.execute_script("return document.documentElement.outerHTML;")
print("DOM retrieved.")
print(dom)

client.quit()
print("Marionette session closed.")
