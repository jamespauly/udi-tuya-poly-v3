import json

import udi_interface
import tinytuya

LOGGER = udi_interface.LOGGER

class TuyaOutletNode(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, device):
        super(TuyaOutletNode, self).__init__(polyglot, primary, address, name)
        self.address = address
        self.name = name
        self.device = device

        if self.device['ip'] is None:
            self.device['ip'] = 'Auto'
        if self.device['ip'] is None:
            self.device['version'] = 3.3

        self.tuya_device = tinytuya.OutletDevice(self.device['id'], self.device['ip'], self.device['key'])
        self.tuya_device.set_version(float(self.device['version']))

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.POLL, self.poll)

    def poll(self, pollType):
        if 'shortPoll' in pollType:
            LOGGER.info('shortPoll (node)')
            self.query()
        else:
            LOGGER.info('longPoll (node)')
            pass

    def query(self):
        LOGGER.info("Query sensor {}".format(self.address))
        LOGGER.info("Node Name {}".format(self.name))
        node_status = self.tuya_device.status()
        LOGGER.info("Node Status {}".format(str(node_status)))
        switch_status = 0
        if node_status['dps']['1']:
            switch_status = 100
        elif not node_status['dps']['1']:
            switch_status = 0
        else:
            switch_status = 101
       
        self.setDriver('GV0', switch_status, True)

    def start(self):
        self.query()

    def cmd_set_on(self, cmd):
        self.tuya_device.set_value('101', 'MODE_MAN_ON')
        self.setDriver('GV0', 100, True)

    def cmd_set_off(self, cmd):
        self.tuya_device.set_value('101', 'MODE_MAN_OFF')
        self.setDriver('GV0', 0, True)

    id = 'tuyanode'

    commands = {
        'ON': cmd_set_on,
        'OFF': cmd_set_off,
        'QUERY': query
    }

    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 2},
        {'driver': 'GV0', 'value': 0, 'uom': 78}
    ]