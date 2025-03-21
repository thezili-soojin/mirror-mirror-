#!/usr/bin/env python

# Copyright (c) 2014 Jason Barrie Morley
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#Mirror-Mirror Google Drive Upload Class! - EunSook

import httplib2
import os
import os.path
import sys
import argparse
import mimetypes
import ConfigParser

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage

import logging

# Check https://developers.google.com/drive/scopes for all available scopes.
OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

# Redirect URI for installed apps.
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

SETTINGS = os.path.expanduser("~/.google-drive-upload")
CONFIGURATION = os.path.join(SETTINGS, "config")
CREDENTIALS = os.path.join(SETTINGS, "credentials")

def components(path):
  """Split a path into its component directories."""
  directory = path
  components = []
  while True:
    (directory, tail) = os.path.split(directory)
    if (tail == ""):
      break
    components.append(tail)
  components.reverse()
  return components

def list_files(drive_service, identifier):

  items = []

  files = drive_service.children().list(folderId=identifier).execute()
  files = files["items"]

  for i in range(len(files)):
    identifier = files[i]["id"]
    f = drive_service.files().get(fileId=identifier).execute()
    items.append(f)

  return items


def get_identifier(drive_service, path):

  print "Finding remote directory..."
  identifier = drive_service.about().get().execute()["rootFolderId"]
  for component in components(path):
    found=False
    files = list_files(drive_service, identifier)
    for f in files:
      if (f["title"] == component):
        identifier = f["id"]
        found=True
        continue
    if not found:
      sys.exit("Unable to find directory.")

  return identifier


def upload(drive_service, path, identifier):

  # Get the name of the file.
  (directory, filename) = os.path.split(path)

  # Determine the mimetype.
  (mime, encoding) = mimetypes.guess_type(path)
  if (mime == None):
    mime = "application/octet-stream"

  # Insert a file
  media_body = MediaFileUpload(path, mimetype=mime, resumable=True)
  body = {
    'title': filename,
    'parents': [{'id': identifier}]
  }

  drive_service.files().insert(body=body, media_body=media_body).execute()


def get_service(client_id, client_secret):

  # Try loading the credentials.
  storage = Storage(CREDENTIALS)
  credentials = storage.get()

  if (credentials == None):

    # Run through the OAuth flow and retrieve credentials
    flow = OAuth2WebServerFlow(client_id, client_secret, OAUTH_SCOPE, REDIRECT_URI)
    authorize_url = flow.step1_get_authorize_url()

    # Attempt to launch the authorization URL in a web browser.
    # If that fails, instruct the user to to launch the browser themselves.
    print 'Go to the following link in your browser: ' + authorize_url
    code = raw_input('Enter verification code: ').strip()
    credentials = flow.step2_exchange(code)

    storage.put(credentials)

  # Create an httplib2.Http object and authorize it with our credentials
  http = httplib2.Http()
  http = credentials.authorize(http)

  # Create the drive service
  drive_service = build('drive', 'v2', http=http)

  return drive_service


def main():
  """Run the script."""
  # parser = argparse.ArgumentParser(description = "Upload a file to Google Drive.")
  # parser.add_argument("file",  nargs='+', help = "File to upload")
  # parser.add_argument("-d", "--directory", help = "Target directory")
  # options = parser.parse_args()
  #
  # logging.basicConfig()
  # logger = logging.getLogger()
  # logger.setLevel('ERROR')
  #
  # # Create the settings directory if it doesn't exist.
  # if (not os.path.exists(SETTINGS)):
  #   os.makedirs(SETTINGS)

  # Load the configuration (client authentication).
  
  if len(sys.argv) == 1:
	  print sys.argv[0]
  elif len(sys.argv) == 2:
	  print sys.argv[1]

  f = sys.argv[1]
  
  config = ConfigParser.ConfigParser()
  config.read(CONFIGURATION)
  client_id = '608630183663-qfod9bmc0a85pf4tckacercqgo02t4ic.apps.googleusercontent.com'
  client_secret = '-pRGgMLNaY2jenTfQnxk2FcD'

  drive_service = None
  try:
    drive_service = get_service(client_id, client_secret)
  except:
    sys.exit("Unable to connect to Google Drive.")

  # Determine the identifier for the destination folder.
  directory = "/"
  # if options.directory:
  #   directory = options.directory 
  identifier = get_identifier(drive_service, directory)

  print('identifier : ' , identifier)
  # for f in 'app.js':
  
  if os.path.exists(f):
    print "Uploading '%s'..." % f

    # Retry uploads three times before giving up and reporting an error.
    retries = 0
    while (True):
      try:
        upload(drive_service, f, identifier)
        break;
      except:
        retries = retries + 1
        if (retries >= 3):
          sys.exit("Failed to upload '%s'." % f)
        else:
          print "Retrying..."

  else:
    sys.exit("Local file '%s' does not exist." % f);

if __name__ == '__main__':
  main()
