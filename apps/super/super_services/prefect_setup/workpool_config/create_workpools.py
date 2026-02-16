#!/usr/bin/env python3
import json
import sys
import os
import copy
import asyncio
from prefect.client.utilities import get_or_create_client
from workpool_defn import WORKPOOLS
from prefect.server.schemas.core import WorkPool
from prefect.server.schemas.actions import WorkPoolUpdate, BlockDocumentCreate
from prefect.exceptions import ObjectNotFound
from tabulate import tabulate

CHECK_MARK = "\u2714"
CROSS_MARK = "\u2718"

OP_WORK_POOL_NAME = 0
OP_WORK_POOL_CREATE_INDEX = 1
OP_WORK_POOL_UPDATE_INDEX = 2
OP_WORK_QUEUE_CREATE_INDEX = 3
OP_WORK_QUEUE_UPDATE_INDEX = 4

SUM_WORK_POOL_NAME = 0
SUM_WORK_QUEUE_NAME = 1
SUM_WORK_POOL_TYPE = 2
SUM_WORK_POOL_CONCURRENCY_LIMIT = 3

DOCKER_CREATE_INDEX = 1
DOCKER_POOL_ADD_INDEX = 2

GITLAB_CRED_CREATE_INDEX = 1
GITLAB_CRED_UPDATE_INDEX = 2
GITLAB_REPO_CREATE_INDEX = 1
GITLAB_REPO_UPDATE_INDEX = 2

DEFAULT_QUEUE_PRIORITY = 100
DOCKER_REGISTRY_NAME = 'oracleregistry'
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local')

TABULATE_OP_ROWS = ['', CROSS_MARK, CROSS_MARK, CROSS_MARK, CROSS_MARK]
TABULATE_SUM_ROWS = ['', '', '', '']

async def get_or_create_docker_registry_credentials(client, docker_registry_user, docker_registry_password, docker_registry_url, docker_rows):
    docker_block_id = None
    docker_schema_id = None
    docker_registry_created_block_id = None
    try:
        docker_block_slug_info = await client.read_block_type_by_slug('docker-registry-credentials')
        docker_block_id = docker_block_slug_info.id
    except ObjectNotFound:
        print('Docker registry block type not found, please create a docker registry block first')
        sys.exit(1)

    docker_block_found = True
    try:
        docker_blocks = await client.read_block_document_by_name(DOCKER_REGISTRY_NAME, 'docker-registry-credentials')
        docker_registry_created_block_id = docker_blocks.id
    except ObjectNotFound:
        docker_block_found = False

    if docker_block_found:
        return docker_registry_created_block_id

    try:
        docker_block_schema_info = await client.read_block_schemas()
        for block_schema in docker_block_schema_info:
            if block_schema.block_type.id == docker_block_id:
                docker_schema_id = block_schema.id
                break
    except ObjectNotFound:
        print('Docker registry block schema not found, please create a docker registry block schema first')
        sys.exit(1)
        
    if docker_schema_id and docker_block_id:
        try:
            creds = {
                'username': docker_registry_user,
                'password': docker_registry_password,
                'registry_url': docker_registry_url,
                'reauth': True
            }
            
            block_document = BlockDocumentCreate(name=DOCKER_REGISTRY_NAME, data=creds, block_schema_id=docker_schema_id, block_type_id=docker_block_id)
            docker_created_block_info = await client.create_block_document(block_document)
            docker_registry_created_block_id = docker_created_block_info.id
            docker_rows[DOCKER_CREATE_INDEX] = CHECK_MARK
        except Exception:
            pass

    return docker_registry_created_block_id

def edit_template_path(update_template_entries, base_job_template, docker_registry_created_block_id,
                             python_path, docker_rows, first_workpool, environment, prefect_api_url, prefect_network):
    block_id = str(docker_registry_created_block_id) if docker_registry_created_block_id else None
    update_template_entries('Docker Registry', base_job_template['variables']['properties']['registry_credentials']['default']['$ref']['block_document_id'], str(block_id), first_workpool)
    base_job_template['variables']['properties']['registry_credentials']['default']['$ref']['block_document_id'] = str(block_id)
    if python_path and ENVIRONMENT == 'local':
        mount_path = f'{python_path}:/opt/prefect/flow_code'
    else:
        mount_path = None
    update_template_entries('Volume Mount Path', base_job_template['variables']['properties']['volumes']['default'][0], mount_path, first_workpool)
    if mount_path is not None:
        base_job_template['variables']['properties']['volumes']['default'][0] = mount_path
    else:
        base_job_template['variables']['properties']['volumes']['default'].clear()
    if docker_registry_created_block_id:
        docker_rows[DOCKER_POOL_ADD_INDEX] = CHECK_MARK
    if environment in ['prod']:
        log_level = 'WARNING'
    else:
        log_level = 'INFO'
    update_template_entries('Logging Level', base_job_template['variables']['properties']['env']['default']['PREFECT_LOGGING_LEVEL'], log_level, first_workpool)
    base_job_template['variables']['properties']['env']['default']['PREFECT_LOGGING_LEVEL'] = log_level
    if prefect_api_url != 'http://127.0.0.1:4200/api':
        update_template_entries('Prefect API URL', base_job_template['variables']['properties']['env']['default']['PREFECT_API_URL'], prefect_api_url, first_workpool)
        base_job_template['variables']['properties']['env']['default']['PREFECT_API_URL'] = prefect_api_url

    update_template_entries('Prefect Network', base_job_template['variables']['properties']['networks']['default'][0], prefect_network, first_workpool)
    base_job_template['variables']['properties']['networks']['default'][0] = prefect_network
    
    hostname = os.environ.get('HOSTNAME', None)
    ip_address = os.environ.get('HOSTNAME_IP', None)
    if hostname and ip_address is not None:  
        extra_args = {
            "extra_hosts": {
                hostname: ip_address
            }
        }
        update_template_entries('Hostname Entries', None, extra_args, first_workpool)
        base_job_template['variables']['properties']['container_create_kwargs']['default'] = extra_args

async def edit_or_update_work_queues(client, pool, pool_name, concurrency_limit, op_row, sum_row):
    total_queues = list()
    if len(pool.get('work_queues', [])) > 0:
        for queue_name, priority in pool['work_queues'].items():
            total_queues.append(f"{queue_name} ({priority})")
            try:
                existing_queue = await client.read_work_queue_by_name(queue_name, pool_name)
            except ObjectNotFound as e:
                existing_queue = None
            except Exception as e:
                print(f"Error checking for existing work queue '{queue_name}' in pool '{pool_name}': {e}")
                continue
            
            if not existing_queue:
                await client.create_work_queue(name=queue_name, work_pool_name=pool_name, concurrency_limit=concurrency_limit)
                op_row[OP_WORK_QUEUE_CREATE_INDEX] = CHECK_MARK
            else:
                await client.update_work_queue(existing_queue.id, name=queue_name, priority=priority, concurrency_limit=concurrency_limit)
                op_row[OP_WORK_QUEUE_UPDATE_INDEX] = CHECK_MARK
                
    try:
        default_queue = await client.read_work_queue_by_name('default', pool_name)
        if default_queue:
            total_queues.append(f"default ({DEFAULT_QUEUE_PRIORITY})")
            await client.update_work_queue(default_queue.id, priority=DEFAULT_QUEUE_PRIORITY, concurrency_limit=concurrency_limit)
            op_row[OP_WORK_QUEUE_UPDATE_INDEX] = CHECK_MARK
    except Exception as e:
        print(f"Error updating default queue in pool '{pool_name}': {e}")
    
    sum_row[SUM_WORK_QUEUE_NAME] = ', '.join(total_queues)
    
async def create_update_workpool(client, pool_name, pool_type, concurrency_limit, base_job_template, op_row, existing_pools):
    pool_exists = any(p.name == pool_name for p in existing_pools)
    if not pool_exists:
        workpool_obj = WorkPool(name=pool_name, type=pool_type, concurrency_limit=concurrency_limit)
        await client.create_work_pool(
            workpool_obj
        )
        op_row[OP_WORK_POOL_CREATE_INDEX] = CHECK_MARK
        
    if pool_type == 'docker' and base_job_template is not None:
        # This is to update the work pool with the base job template 
        # incase pool exists we update only concurrency limit because existing changes would be overwritten
        kwargs = {
            "base_job_template": base_job_template,
            "concurrency_limit": concurrency_limit
        }
        workpool_update_obj = WorkPoolUpdate(**kwargs)
        await client.update_work_pool(pool_name, workpool_update_obj)
        op_row[OP_WORK_POOL_UPDATE_INDEX] = CHECK_MARK
    
async def get_prefect_client():
    client = None
    for i in range(5):
        try:
            client = get_or_create_client()
            client = client[0]
            await client.hello()
            return client
        except Exception as e:
            print(f"Failed to connect to API: {e} retrying..., attempt {i + 1}/5")
            await asyncio.sleep(5)
    
    if client is None:
        print('Failed to connect prefect server, returning error')
        sys.exit(1)

async def create_workpools():
    
    # Check if API is available
    client = await get_prefect_client()
        
    docker_registry_user = os.environ.get('DOCKER_REGISTRY_USER', None)
    docker_registry_password = os.environ.get('DOCKER_REGISTRY_PASSWORD', None)
    docker_registry_url = os.environ.get('DOCKER_REGISTRY_URL', None)
    
    # gitlab_access_token = os.environ.get('GITLAB_ACCESS_TOKEN', None)
    if not docker_registry_user or not docker_registry_password or not docker_registry_url:
        print('Docker registry credentials not found in environment variables, please set DOCKER_REGISTRY_USER, DOCKER_REGISTRY_PASSWORD and DOCKER_REGISTRY_URL')
        sys.exit(1)
        
    # if ENVIRONMENT != 'local' and (not gitlab_access_token):
    #     print('Gitlab access token not found in environment variables, please set GITLAB_ACCESS_TOKEN')
    #     sys.exit(1)
    
    tabulate_docker_headers = ['Docker Registry', 'Created', 'Added to Pool']
    
    tabulate_gitlab_creds_headers = ['Gitlab Creds', 'Created', 'Updated']
    tabulate_gitlab_repo_headers = ['Gitlab Repo', 'Created', 'Updated']

    tabulate_sum_headers = ['Work Pool Name', 'Work Queues (Priority)', 'Type', 'Concurrency Limit']
    tabulate_op_headers = ['Work Pool Name', 'Created', 'Updated', 'Queue Created', 'Queue Updated']
    
    tabulate_update_template_headers = ['Entry Name', 'Old Value', 'New Value']

    docker_rows = [DOCKER_REGISTRY_NAME, CROSS_MARK, CROSS_MARK]
    
    template_update_entries = list()
    environment = os.environ.get('ENVIRONMENT', 'local')
    prefect_api_url = os.environ.get('PREFECT_API_URL', 'http://127.0.0.1:4200/api')
    prefect_network = os.environ.get('PREFECT_NETWORK', 'prefect-network')
    update_template_entries = lambda entry, old_value, new_value, first_entry: template_update_entries.append([entry, old_value, new_value]) if first_entry  else template_update_entries

    docker_registry_created_block_id = await get_or_create_docker_registry_credentials(client, docker_registry_user, docker_registry_password, docker_registry_url, docker_rows)

    python_path = os.environ.get('MOUNTPATH', None)
    
    sum_total_rows = list()
    op_total_rows = list()
    existing_pools = await client.read_work_pools()
    first_workpool = True
    for pool in WORKPOOLS:
        try:
            sum_row = copy.deepcopy(TABULATE_SUM_ROWS)
            op_row = copy.deepcopy(TABULATE_OP_ROWS)
            
            pool_name = pool["name"]
            pool_type = pool["type"]
            template_path = pool["base_job_template"]
            concurrency_limit = pool['concurrency_limit']
            base_job_template = None

            sum_row[SUM_WORK_POOL_NAME] = pool_name
            sum_row[SUM_WORK_POOL_TYPE] = pool_type
            sum_row[SUM_WORK_POOL_CONCURRENCY_LIMIT] = 'Unlimited' if concurrency_limit == None else concurrency_limit
            op_row[OP_WORK_POOL_NAME] = pool_name
            
            if os.path.exists(template_path):
                with open(template_path, "r") as f:
                    base_job_template = json.load(f)

                edit_template_path(update_template_entries, base_job_template, docker_registry_created_block_id,
                                         python_path, docker_rows, first_workpool, environment, prefect_api_url, prefect_network)
                
            await create_update_workpool(client, pool_name, pool_type, concurrency_limit, base_job_template, op_row, existing_pools)
            await edit_or_update_work_queues(client, pool, pool_name, concurrency_limit, op_row, sum_row)
        except Exception as e:
            print(f"Error handling work pool {pool['name']}: {e}")
        finally:
            sum_total_rows.append(sum_row)
            op_total_rows.append(op_row)
            first_workpool = False
    
    print('Docker Registry Information:')
    print(tabulate([docker_rows], headers=tabulate_docker_headers, tablefmt='fancy_grid'))
    
    print('Workpool Summary Information:')
    print(tabulate(sum_total_rows, headers=tabulate_sum_headers, tablefmt='fancy_grid'))
    
    print('Workpool Operation Information:')
    print(tabulate(op_total_rows, headers=tabulate_op_headers, tablefmt='fancy_grid'))
    
    print('Updated Work Pool Entries:')
    print(tabulate(template_update_entries, headers=tabulate_update_template_headers, tablefmt='fancy_grid'))

if __name__ == "__main__":
    asyncio.run(create_workpools())