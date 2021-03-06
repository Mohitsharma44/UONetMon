"""UOController Vis controller."""

import os
import ast
import sys
import json
from colorama import init, Fore, Back, Style
from cement.ext.ext_argparse import ArgparseController, expose
from uocontroller.cli.controllers.rpc_client import UOControllerRpcClient

init(autoreset=True)

#known_vis_queues = {
#        "1mtcNorth": "1mtcNorth_vis_queue",
#        "1mtcSouth": "1mtcSouth_vis_queue",
#        "370Roof"  : "370Roof_vis_queue",
#        "test"     : "test_vis_queue"
#    }

known_vis_queues = {
    "1mtcNorth": {"cam": "1mtcNorth", "watchdog": "1mtcNorth_watchdog"},
    "1mtcSouth": {"cam": "1mtcSouth", "watchdog": "1mtcSouth_watchdog"},
    "370Roof"  : {"cam": "370Roof", "watchdog": "370Roof_watchdog"},
    "test"     : {"cam": "test", "watchdog": "test_watchdog"},
    }

class QueueNameException(Exception):
    pass

class UOControllerVisController(ArgparseController):
    class Meta:
        label = 'VIS'
        description = 'Controller for Vis cameras'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['-l', '--loc'],
             dict(help='location of the cameras. e.g: \n\t 1mtcNorth \n\t 1mtcSouth \n\t 370Roof(WIP) \n\t test(WIP)',
                  dest='loc', action='store', metavar='String') ),
            (['-c', '--capture'],
             dict(help="capture X frames (use -1 to capture forever)", dest='capture', action='store',
                  default=0, const=0, nargs='?', metavar='Int')),
            (['--every', '--every'],
             dict(help="perform capture every X seconds. default is 10s", dest='every', action='store',
                  metavar='Int', default=0, const=0, nargs='?')),
            (['--live', '--live'],
             dict(help="Open Live Feed to the camera (Not Implemented)", dest='live', action='store_true')),
            (['-f', '--focus'],
             dict(help="Focus the vis camera camera. options=<absolute value>", dest='focus', action='store',
                  metavar='float', default=-1, const=-1, nargs='?')),
            (['-a', '--aperture'],
             dict(help="Adjust the aperture of the camera. options=<absolute value>", dest='aper', action='store',
                  metavar='float', default=-1, const=-1, nargs='?')),
            (['-s', '--stop'],
             dict(help="Abort and Stop acquiring images", dest='stop', action='store_true', default=0)),
            (['-stat', '--status'],
             dict(help="Current Status of the camera and its driver", dest='stat', action='store_true', default=False)),
            (['-e', '--exposure'],
             dict(help="Adjust the exposure of the camera. options=<absolute value>", dest='exp', action='store',
                  metavar='float', default=-1, const=-1, nargs='?')),
            (['--kill', '--kill'],
             dict(help="""This will kill the code driving the camera on the remote end. Make sure you do want to
             do this. There is a chance that the driving code will be restarted automatically but cannot be
             guaranteed.""", dest='kill', action='store', default='', metavar='String')),
            ]

    def _generate_data(self):
        return {
            "location": self.app.pargs.loc,
            "capture": int(self.app.pargs.capture),
            "interval": int(self.app.pargs.every),
            "focus": int(self.app.pargs.focus),
            "aperture": int(self.app.pargs.aper),
            "exposure": float(self.app.pargs.exp),
            "stop": bool(self.app.pargs.stop),
            "status": bool(self.app.pargs.stat),
            "kill": str(self.app.pargs.kill)
            }

    @expose(hide=True)
    def default(self):
        if not self.app.pargs.loc in known_vis_queues.keys():
            raise QueueNameException("Check the location name format!!")
        
        vis_cam_rpc_client = UOControllerRpcClient(vhost="/vis",
                                               queue_name=known_vis_queues[self.app.pargs.loc]["cam"])
        vis_watchdog_rpc_client = UOControllerRpcClient(vhost="/vis",
                                                        queue_name=known_vis_queues[self.app.pargs.loc]["watchdog"])

        print("Inside UOControllerVisController.default().")
        # Generate Json structured command
        print(Fore.BLUE + "=="*30)
        try:
            if not self.app.pargs.loc:
                print("You need to pass the location")
                sys.exit(1)
            command = self._generate_data()
            cam_response = vis_cam_rpc_client.call(json.dumps(command))
            try:
                #print(response)
                json_cam_response = ast.literal_eval(cam_response.strip("b'"))
                #print(json.dumps(json_response, indent=4))
                try:
                    for (k, v) in json_cam_response.items():
                        if "err" in k:
                            print("{0: <16}==>{1}{2: ^16}".format(k, Fore.RED, v))
                        elif "capture" == k:
                            if v == -1:
                                print("{0: <16}==>{1}{2: ^16}".format(k, Fore.GREEN, "Continuous"))
                            elif v == 0:
                                print("{0: <16}==>{1: ^16}".format(k, "(Not Live)"))
                            else:
                                print("{0: <16}==>{1}{2: ^16}(Remaining)".format(k, Fore.GREEN, v))
                        else:
                            print("{0: <16}==>{1: ^16}".format(k, v))
                except Exception as ex:
                    print(cam_response)
            except Exception as ex:
                pass
            finally:
                try:
                    watchdog_response = vis_watchdog_rpc_client.call(json.dumps(command))
                    print()
                    print("==Watchdog==")
                    print(watchdog_response)
                    #json_watchdog_response = ast.literal_eval(watchdog_response.strip("b'"))
                except Exception as ex:
                    print("Error sending RPC request to watchdog: "+str(ex))
        except Exception as ex:
            print("Error generating json structured command: ", str(ex))
        print(Fore.BLUE + "=="*30)
        if self.app.pargs.live:
            print("Feture not implemented ... ")

        # If using an output handler such as 'mustache', you could also
        # render a data dictionary using a template.  For example:
        #
        #   data = dict(foo='bar')
        #   self.app.render(data, 'default.mustache')
        #
        #
        # The 'default.mustache' file would be loaded from
        # ``uocontroller.cli.templates``, or ``/var/lib/uocontroller/templates/``.
        #
