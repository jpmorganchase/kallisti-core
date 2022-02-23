import copy


class Sanitizer:
    SENSITIVE_KEYS = ['auth', 'token', 'password', 'cookie']  # 'key']
    REPLACEMENT_VALUE = '*****'

    @staticmethod
    def clean_sensitive_data(data):
        if isinstance(data, list):
            result = []
            for i in data:
                item = Sanitizer.clean_sensitive_data(i) \
                    if isinstance(i, dict) or isinstance(i, list) else i
                result.append(item)
            return result
        elif isinstance(data, dict):
            result = {}
            for k, v in Sanitizer.replace_dict_values_if_sensitive(data)\
                    .items():
                result[k] = Sanitizer.clean_sensitive_data(v)\
                    if isinstance(v, dict) or isinstance(v, list) else v
            return result
        else:
            return data

    @staticmethod
    def replace_dict_values_if_sensitive(data: dict):
        d = copy.deepcopy(data)
        for k, v in d.items():
            if isinstance(v, str) and Sanitizer.has_sensitive_key(k.lower()):
                d[k] = Sanitizer.REPLACEMENT_VALUE
        return d

    @staticmethod
    def has_sensitive_key(s: str):
        for key in Sanitizer.SENSITIVE_KEYS:
            if key in s:
                return True
        return False
