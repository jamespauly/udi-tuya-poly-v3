import udi_interface
import tinytuya
import json
import time

from nodes import TuyaNode, TuyaOutletNode

# IF you want a different log format than the current default
LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom


class TuyaController(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(TuyaController, self).__init__(polyglot, primary, address, name)
        self.cloud_config_obj = None
        self.devices_obj = None
        self.poly = polyglot
        self.name = name
        self.primary = primary
        self.address = address
        self.n_queue = []

        self.Notices = Custom(polyglot, 'notices')
        self.Parameters = Custom(polyglot, 'customparams')

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.parameter_handler)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)

        self.poly.ready()
        self.poly.addNode(self)

    def node_queue(self, data):
        self.n_queue.append(data['address'])

    def wait_for_node_event(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()

    def parameter_handler(self, params):
        self.Notices.clear()
        self.Parameters.load(params)
        if self.Parameters['devices'] is not None:
            devices = self.Parameters['devices']
            self.devices_obj = json.loads(devices);
        if self.Parameters['cloud_config'] is not None:
            cloud_config = self.Parameters['cloud_config']
            self.cloud_config_obj = json.loads(cloud_config);
        # self.check_params()

    def start(self):
        LOGGER.info('Staring Tuya NodeServer')
        self.poly.updateProfile()
        self.poly.setCustomParamsDoc()
        self.discover()

    def query(self, command=None):
        LOGGER.info("Query sensor {}".format(self.address))
        self.discover()

    def discover(self, *args, **kwargs):
        LOGGER.info("Starting Tuya Device Discovery")
        if self.Parameters['devices'] is not None:
            self.devices_obj = json.loads(self.Parameters['devices'])
            for device in self.devices_obj:
                if device['product_name'].lower() == 'smart outdoor plug':
                    self.poly.addNode(
                        TuyaOutletNode(self.poly, self.address, device['mac'].replace(':', ''), device['name'], device))
                    self.wait_for_node_event()
        elif self.Parameters['devices'] is None and self.cloud_config_obj is not None:
            cloud = tinytuya.Cloud(**self.cloud_config_obj)
            devices = cloud.getdevices(include_map=True)
            scan_results = tinytuya.deviceScan()
            LOGGER.debug(devices)
            self.devices_obj = json.loads(devices)
            for device in self.devices_obj:
                if device['product_name'].lower() == 'smart outdoor plug':
                    for sr in scan_results:
                        if scan_results[sr]['id'] == device['id']:
                            device['ip'] = scan_results[sr]['ip']
                            device['version'] = scan_results[sr]['version']
                    self.poly.addNode(
                        TuyaOutletNode(self.poly, self.address, device['mac'].replace(':', ''), device['name'], device))
                    self.wait_for_node_event()

        LOGGER.info('Finished Tuya Device Discovery')

    def delete(self):
        LOGGER.info('Deleting Tuya Node Server')

    def stop(self):
        nodes = self.poly.getNodes()
        for node in nodes:
            if node != 'controller':  # but not the controller node
                nodes[node].setDriver('ST', 0, True, True)
        self.poly.stop()
        LOGGER.info('Daikin Tuya stopped.')

    id = 'tuya'
    commands = {
        'QUERY': query,
        'DISCOVER': discover
    }

    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 2}
    ]
