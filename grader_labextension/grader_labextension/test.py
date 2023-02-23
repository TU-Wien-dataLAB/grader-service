# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from grader_labextension.registry import HandlerPathRegistry
import tornado

# run __init__.py to register handlers
import grader_labextension

def main():
  """
  Runs the GraderExtensionHandler tornado server locally without being attached to a jupyter_server.
  """
  print("Starting Extension handler... ", end="")
  handlers = HandlerPathRegistry.handler_list()
  app = tornado.web.Application(handlers, debug=True)
  print("Done")
  app.listen(4010)
  tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
  main()