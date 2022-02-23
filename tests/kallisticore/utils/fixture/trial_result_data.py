from kallisticore.utils.sanitizer import Sanitizer

sanitizer_theoretical_test = {
    'a': 'a',
    'b_auth': 'my-sensitive-secret',
    'c': {
        'a_token': 'my-sensitive-secret',
        'b': {
            'a': 'a',
            'b_token_a': 'my-sensitive-secret'
        }
    }
}

sanitizer_theoretical_test_expected = {
    'a': 'a',
    'b_auth': Sanitizer.REPLACEMENT_VALUE,
    'c': {
        'a_token': Sanitizer.REPLACEMENT_VALUE,
        'b': {
            'a': 'a',
            'b_token_a': Sanitizer.REPLACEMENT_VALUE
        }
    }
}

sanitizer_real_example_test = {
    'id': 'test-id',
    'seal_id': '123456',
    'metadata': {},
    'ticket': {},
    'parameters': {},
    'trial_record': {
        'pre_steps': [
            {
                'step_name': 'Http probe',
                'step_parameters': {
                    'url': 'https://test-url.com',
                    'headers': {
                        'authorization': 'bearer my-sensitive-secret',
                        'Content-Type': 'application/json',
                        'session-id': 'test-session-id',
                        'trace-id': 'test-trace-id',
                        'x-test-channel': 'abc',
                        'userid': 'from-postman', 'user-agent': 'System'
                    }
                },
                'logs': [
                    'log-text-1',
                    'log-text-2',
                ]
            },
            {
                'step_name': 'Enable chaosmonkey',
                'step_parameters': {
                    'base_url': 'https://test-url.com',
                    'headers': {
                        'authorization': 'bearer my-sensitive-secret'
                    },
                    'platform': {
                        'type': 'test-type',
                        'pool': 'test-pool',
                        'env': 'test-env',
                        'org_name': 'test-org',
                        'app_name': 'test-app-name'
                    }
                },
                'logs': [
                    'test-log-line-1',
                    'test-log-line-2'
                ]
            }
        ],
        'result': [
            {
                'logs':
                    [
                        'test-log-line-1'
                    ]
            }
        ]
    },
    'status': 'Aborted',
    'executed_at': '2019-10-16T19:00:36.000000Z',
    'completed_at': '2019-10-16T19:00:42.000000Z',
    'initiated_by': 'test-initiated-by',
    'experiment': {
        'id': 'test-experiment-id',
        'name': 'test-experiment-name',
        'description': 'test-experiment-desc',
        'metadata': {},
        'parameters': {
            'app_base_url': 'https://test-url.com',
            'app_auth_token': 'my-sensitive-secret',
            'business_url': 'https://test-business-url.com'
        },
        'pre_steps': [
            {
                'step': 'Check businessurl endpoint',
                'do': 'cm.http_probe',
                'where': {
                    'url': '{{ business_url }}',
                    'headers': {
                        'authorization': 'bearer my-sensitive-secret',
                        'Content-Type': 'application/json',
                        'session-id': 'test-session-id',
                        'trace-id': 'test-trace-id',
                        'x-test-channel': 'abc',
                        'userid': 'from-postman',
                        'user-agent': 'System'
                    }
                }
            },
            {
                'step': 'Enable chaos-monkey for retail-intake',
                'do': 'sb.enable_chaosmonkey',
                'where': {
                    'base_url': '{{ app_base_url }}',
                    'headers': {
                        'authorization': 'bearer my-sensitive-secret'
                    },
                    'platform': {
                        'type': 'test-type',
                        'pool': 'test-pool',
                        'env': 'test-env',
                        'org_name': 'test-org',
                        'app_name': 'test-app-name'
                    }
                }
            },
            {
                'step': 'Check chaos-monkey status',
                'do': 'cm.http_probe',
                'where': {
                    'headers': {
                        'authorization': 'bearer my-sensitive-secret'
                    },
                    'url': '{{ app_base_url }}/chaosmonkey/status'
                }
            },
            {
                'step': 'Configure assaults',
                'do': 'sb.change_assaults_configuration',
                'where': {
                    'base_url': '{{ app_base_url }}',
                    'headers': {
                        'authorization': 'bearer my-sensitive-secret'
                    },
                    'platform': {
                        'type': 'test-type',
                        'pool': 'test-pool',
                        'env': 'test-env',
                        'org_name': 'test-org',
                        'app_name': 'test-app-name'
                    },
                    'assaults_configuration': {
                        'level': 1, 'latencyRangeStart': 1,
                        'latencyRangeEnd': 10,
                        'latencyActive': False,
                        'exceptionsActive': True,
                        'killApplicationActive': False,
                        'restartApplicationActive': False,
                        'watchedCustomServices': [
                            'test-watched-service-1'
                        ],
                        'exception': {
                            'type': 'java.lang.NullPointerException',
                            'arguments': [
                                {
                                    'className': 'java.lang.String',
                                    'value': 'No engine'
                                }
                            ]
                        }
                    }
                }
            },
            {
                'step': 'Check businessurl endpoint',
                'do': 'cm.http_probe',
                'where': {
                    'url': '{{ business_url }}',
                    'headers': {
                        'authorization': 'bearer my-sensitive-secret',
                        'Content-Type': 'application/json',
                        'session-id': 'test-session-id',
                        'trace-id': 'test-trace-id',
                        'x-test-channel': 'abc',
                        'userid': 'from-postman',
                        'user-agent': 'System'
                    }
                }
            }
        ],
        'steps': [],
        'post_steps': [],
        'created_by': 'test-created-by'
    },
    'platform_type': 'cf',
    'platform_info': {
        'cf_org': 'test-cf-org',
        'cf_pool': 'test-cf-pool',
        'cf_space': 'test-cf-space',
        'cf_app_guid': 'test-cf-app-guid'
    }
}

sanitizer_real_example_test_expected = {
    'id': 'test-id',
    'seal_id': '123456',
    'metadata': {},
    'ticket': {},
    'parameters': {},
    'trial_record': {
        'pre_steps': [
            {
                'step_name': 'Http probe',
                'step_parameters': {
                    'url': 'https://test-url.com',
                    'headers': {
                        'authorization': Sanitizer.REPLACEMENT_VALUE,
                        'Content-Type': 'application/json',
                        'session-id': 'test-session-id',
                        'trace-id': 'test-trace-id',
                        'x-test-channel': 'abc',
                        'userid': 'from-postman', 'user-agent': 'System'
                    }
                },
                'logs': [
                    'log-text-1',
                    'log-text-2',
                ]
            },
            {
                'step_name': 'Enable chaosmonkey',
                'step_parameters': {
                    'base_url': 'https://test-url.com',
                    'headers': {
                        'authorization': Sanitizer.REPLACEMENT_VALUE
                    },
                    'platform': {
                        'type': 'test-type',
                        'pool': 'test-pool',
                        'env': 'test-env',
                        'org_name': 'test-org',
                        'app_name': 'test-app-name'
                    }
                },
                'logs': [
                    'test-log-line-1',
                    'test-log-line-2'
                ]
            }
        ],
        'result': [
            {
                'logs':
                    [
                        'test-log-line-1'
                    ]
            }
        ]
    },
    'status': 'Aborted',
    'executed_at': '2019-10-16T19:00:36.000000Z',
    'completed_at': '2019-10-16T19:00:42.000000Z',
    'initiated_by': 'test-initiated-by',
    'experiment': {
        'id': 'test-experiment-id',
        'name': 'test-experiment-name',
        'description': 'test-experiment-desc',
        'metadata': {},
        'parameters': {
            'app_base_url': 'https://test-url.com',
            'app_auth_token': Sanitizer.REPLACEMENT_VALUE,
            'business_url': 'https://test-business-url.com'
        },
        'pre_steps': [
            {
                'step': 'Check businessurl endpoint',
                'do': 'cm.http_probe',
                'where': {
                    'url': '{{ business_url }}',
                    'headers': {
                        'authorization': Sanitizer.REPLACEMENT_VALUE,
                        'Content-Type': 'application/json',
                        'session-id': 'test-session-id',
                        'trace-id': 'test-trace-id',
                        'x-test-channel': 'abc',
                        'userid': 'from-postman',
                        'user-agent': 'System'
                    }
                }
            },
            {
                'step': 'Enable chaos-monkey for retail-intake',
                'do': 'sb.enable_chaosmonkey',
                'where': {
                    'base_url': '{{ app_base_url }}',
                    'headers': {
                        'authorization': Sanitizer.REPLACEMENT_VALUE
                    },
                    'platform': {
                        'type': 'test-type',
                        'pool': 'test-pool',
                        'env': 'test-env',
                        'org_name': 'test-org',
                        'app_name': 'test-app-name'
                    }
                }
            },
            {
                'step': 'Check chaos-monkey status',
                'do': 'cm.http_probe',
                'where': {
                    'headers': {
                        'authorization': Sanitizer.REPLACEMENT_VALUE
                    },
                    'url': '{{ app_base_url }}/chaosmonkey/status'
                }
            },
            {
                'step': 'Configure assaults',
                'do': 'sb.change_assaults_configuration',
                'where': {
                    'base_url': '{{ app_base_url }}',
                    'headers': {
                        'authorization': Sanitizer.REPLACEMENT_VALUE
                    },
                    'platform': {
                        'type': 'test-type',
                        'pool': 'test-pool',
                        'env': 'test-env',
                        'org_name': 'test-org',
                        'app_name': 'test-app-name'
                    },
                    'assaults_configuration': {
                        'level': 1, 'latencyRangeStart': 1,
                        'latencyRangeEnd': 10,
                        'latencyActive': False,
                        'exceptionsActive': True,
                        'killApplicationActive': False,
                        'restartApplicationActive': False,
                        'watchedCustomServices': [
                            'test-watched-service-1'
                        ],
                        'exception': {
                            'type': 'java.lang.NullPointerException',
                            'arguments': [
                                {
                                    'className': 'java.lang.String',
                                    'value': 'No engine'
                                }
                            ]
                        }
                    }
                }
            },
            {
                'step': 'Check businessurl endpoint',
                'do': 'cm.http_probe',
                'where': {
                    'url': '{{ business_url }}',
                    'headers': {
                        'authorization': Sanitizer.REPLACEMENT_VALUE,
                        'Content-Type': 'application/json',
                        'session-id': 'test-session-id',
                        'trace-id': 'test-trace-id',
                        'x-test-channel': 'abc',
                        'userid': 'from-postman',
                        'user-agent': 'System'
                    }
                }
            }
        ],
        'steps': [],
        'post_steps': [],
        'created_by': 'test-created-by'
    },
    'platform_type': 'cf',
    'platform_info': {
        'cf_org': 'test-cf-org',
        'cf_pool': 'test-cf-pool',
        'cf_space': 'test-cf-space',
        'cf_app_guid': 'test-cf-app-guid'
    }
}
