import pytest
from sentential.lib.clients import clients

@pytest.fixture(scope="class")
def gw_domains():
    api = clients.api_gw.create_api(
        Name='testing',
        ProtocolType='HTTP',
        Tags={
            'sentential': ''
        },
    )

    domain = clients.api_gw.create_domain_name(
        DomainName="dev.testing.io",
        Tags={
            'sentential': ''
        }
    )

    for mapping_key in ["v1", "v2"]:
        clients.api_gw.create_api_mapping(
            ApiId=api['ApiId'],
            ApiMappingKey=mapping_key,
            DomainName=domain['DomainName'],
            Stage="$default"
        )

    yield

    clients.api_gw.delete_domain_name(DomainName="dev.testing.io")
    clients.api_gw.delete_api(ApiId=api['ApiId'])
