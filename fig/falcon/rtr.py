from .errors import ApiError, RTRError, RTRConnectionError


class RTRSession:
    def __init__(self, falcon_api, device_id):
        self.falcon = falcon_api
        self.device_id = device_id
        self.session = self._connect()

    def close(self):
        return self.falcon._resources(
            action='RTR_DeleteSession',
            parameters={
                'session_id': self.id
            }
        )

    def execute_and_wait(self, action, base_command, command_string):
        command = self._execute(action, base_command, command_string)
        response = self._rtr_wait(command[0])

        if response['stderr']:
            raise RTRError(f'RTR Execute device: {self.device_id}, stderr: {response["stderr"]}')
        return response

    def get_file(self, filepath):
        command = self.execute_and_wait('RTR_ExecuteActiveResponderCommand', 'get', 'get ' + filepath)
        for f in self._list_files():
            if f['cloud_request_id'] == command['task_id']:
                return self._fetch_file(f['sha256'], filepath)

        raise RTRError(f'RTR File Not Found: device: {self.device_id}, file {filepath}')

    @property
    def id(self):
        return self.session['session_id']

    def _list_files(self):
        return self.falcon._resources(
            'RTR_ListFiles',
            parameters={
                'session_id': self.id
            }
        )

    def _fetch_file(self, sha256, filepath):
        response = self.falcon.client.command(
            'RTR_GetExtractedFileContents',
            parameters={
                'session_id': self.id,
                'sha256': sha256,
                'filepath': filepath,
            }
        )
        if not isinstance(response, (bytes, bytearray)):
            raise RTRError(f"Could not fetch RTR file from Falcon: {response['body']}")
        return response

    def _connect(self):
        response = None
        try:
            response = self.falcon.init_rtr_session(self.device_id)
        except ApiError as e:
            raise RTRConnectionError(f"{e}")

        if len(response) != 1:
            raise RTRError(f'Unexpected response from RTR Init: {response}')
        return response[0]

    def _rtr_wait(self, command):
        check = self.falcon.check_rtr_command_status(command['cloud_request_id'], 0)[0]
        while not check['complete']:
            check = self.falcon.check_rtr_command_status(command['cloud_request_id'], 0)[0]
        return check

    def _execute(self, action, base_command, command_string):
        return self.falcon.execute_rtr_command(action, self.id, base_command, command_string)
