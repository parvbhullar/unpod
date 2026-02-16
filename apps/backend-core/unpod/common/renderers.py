from rest_framework.renderers import JSONRenderer


class UnpodJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response_data = {}
        response = renderer_context.get("response", None)

        # Handle None data case
        if data is None:
            data = {}

        if response.status_code >= 401:
            response_data = {}
            if 'detail' in data:
                response_data['message'] = data.pop('detail')
                response_data['status_code'] = response.status_code
            response_data.update(data)
            response = super(UnpodJSONRenderer, self).render(response_data, accepted_media_type, renderer_context)
            return response

        message = 'Success'
        if 'count' in data:
            response_data['count'] = data.pop('count')
        if 'unread_count' in data:
            response_data['unread_count'] = data.pop('unread_count')
        if 'message' in data:
            message = data.pop('message')
        if 'success' in data and type(data['success']) == str:
            message = data.pop('success')
        response_data['status_code'] = response.status_code
        response_data['message'] = message
        if 'url_redirect' in data and 'url' in data:
            response_data['url_redirect'] = data.pop('url_redirect')
            response_data['url'] = data.pop('url')

        success = 200 <= response.status_code <= 202 or response.status_code in [204, 302]
        data_data = {}
        if 'data' not in data:
            response_data['data'] = data or {}
        else:
            data_data = data.pop('data', {})
            response_data['data'] = data_data
        if not success:
            response_data['data'] = {}
            if 'error' in data:
                response_data['message'] = data.pop('error')
            if response_data['message'] == 'Success':
                response_data['message'] = 'Error'
            if len(data_data):
                response_data['data'] = data_data
            if len(data):
                response_data['data'].update(data)
        if 'errors' in data:
            response_data['errors'] = data['errors']
        # response_data.update(data)
        response = super(UnpodJSONRenderer, self).render(response_data, accepted_media_type, renderer_context)
        return response
