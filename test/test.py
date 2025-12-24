import asyncio
from aclient import *

# TEST_CREATE_TASK_FROM_URL = True
TEST_CREATE_TASK_FROM_URL = False

# TEST_GET_TASK = True
TEST_GET_TASK = False

TEST_DOWNLOAD = True
# TEST_DOWNLOAD = False


async def test_create_task_from_url(mu_client):
    print('TEST: 从URL创建单个文件解析任务 ...')
    result = []
    urls = [
        'https://cdn.jsdelivr.net/gh/Ar-Hyk/MinerU-Api@dev/test/demo1.pdf',
        'https://cdn.jsdelivr.net/gh/Ar-Hyk/MinerU-Api@dev/test/demo2.pdf',
        'https://cdn.jsdelivr.net/gh/Ar-Hyk/MinerU-Api@dev/test/demo3.pdf',
        'https://cdn.jsdelivr.net/gh/Ar-Hyk/MinerU-Api@dev/test/small_ocr.pdf',
    ]

    print(f'测试 [{urls[0]}] ...')
    req = RequestUrlFile(url=urls[0])
    req.model_version = ModelVersion.VLM
    print(req)
    # RequestUrlFile(url='https://cdn.jsdelivr.net/gh/Ar-Hyk/MinerU-Api@dev/test/demo1.pdf', model_version=<ModelVersion.VLM: 'vlm'>)
    res = await mu_client.create_task_from_url(req=req)
    print(res)
    # Response(code=0, msg='ok', data={'task_id': 'c327610b-576c-4ece-b636-a0596bea8d0d'}, trace_id='1af8bebd1fd383a301820dc8d4eac36d')
    result += res.task_id
    print(f'测试 [{urls[0]}] 通过！task_id={res.task_id}')


    print(f'测试 [{urls[1]}] ...')
    res = await mu_client.create_task_from_url(url=urls[1])
    print(res)
    # Response(code=0, msg='ok', data={'task_id': '60a1e367-3099-4feb-8776-9412b755120b'}, trace_id='5b4b46f364b9edd024c1066d6b42621a')+
    print(f'测试 [{urls[1]}] 通过！task_id={res.task_id}')
    result += res.task_id
    print('Success! TEST: 从URL创建单个文件解析任务')
    return result

async def test_get_task(mu_client, task_id):
    print('TEST: 获取任务详情 ...')
    result = []
    for task in task_id:
        task_info = await mu_client.get_task(task)
        result += task_info
        print(task_info)
        # TaskInfo(task_id='c327610b-576c-4ece-b636-a0596bea8d0d', status='done', err_msg='', extract_progress=None, full_zip_url='https://cdn-mineru.openxlab.org.cn/pdf/2025-12-17/ace5cabc-3eab-4f29-883f-43c5e722e8a6.zip', model_version='vlm2.6.5')
        # TaskInfo(task_id='60a1e367-3099-4feb-8776-9412b755120b', status='pending', err_msg='', extract_progress=None, full_zip_url=None, model_version='pipeline2.6.5')
        # TaskInfo(task_id='60a1e367-3099-4feb-8776-9412b755120b', status='done', err_msg='', extract_progress=None, full_zip_url='https://cdn-mineru.openxlab.org.cn/pdf/2025-12-24/c11d9fa5-69d0-46f9-94d9-30d0e9602962.zip', model_version='pipeline2.6.5')
    print('Success! TEST: 获取任务详情')
    return result


async def test_download(mu_client, task_info:list[TaskInfo]):
    print('TEST: 下载任务 ...')
    for task in task_info:
        print(f'测试 {task.task_id} ...')
        if task.is_done:
            path = await mu_client.download(task, '../data')
            print(f'测试 [{task.task_id}] 通过！path：{path}')
    print('Success! TEST: 下载任务')

async def main():
    async with AsyncMinerUClient() as mu_client:
        # TEST: 从URL创建单个文件解析任务
        if TEST_CREATE_TASK_FROM_URL:
            task_id = await test_create_task_from_url(mu_client)
        else:
            task_id = ['c327610b-576c-4ece-b636-a0596bea8d0d', '60a1e367-3099-4feb-8776-9412b755120b']

        # TEST: 获取任务详情
        if TEST_GET_TASK:
            task_info = await test_get_task(mu_client, task_id)
        else:
            task_info = [
                TaskInfo(task_id='c327610b-576c-4ece-b636-a0596bea8d0d', status='done', err_msg='', extract_progress=None, full_zip_url='https://cdn-mineru.openxlab.org.cn/pdf/2025-12-17/ace5cabc-3eab-4f29-883f-43c5e722e8a6.zip', model_version='vlm2.6.5'),
                TaskInfo(task_id='60a1e367-3099-4feb-8776-9412b755120b', status='pending', err_msg='', extract_progress=None, full_zip_url=None, model_version='pipeline2.6.5'),
                TaskInfo(task_id='60a1e367-3099-4feb-8776-9412b755120b', status='done', err_msg='', extract_progress=None, full_zip_url='https://cdn-mineru.openxlab.org.cn/pdf/2025-12-24/c11d9fa5-69d0-46f9-94d9-30d0e9602962.zip', model_version='pipeline2.6.5')
            ]


        # TEST: 下载任务
        if TEST_DOWNLOAD:await test_download(mu_client, task_info)


        # fs_info = RequestUploadFiles(files=[
        #     FileInfo('demo1.pdf',data_id='test', file_path='demo1.pdf'),
            # FileInfo('example.pdf',data_id='test', file_path='example.pdf'),
            # FileInfo('test.pdf',data_id='Test None', file_path='test.pdf')
        # ])
        # print(fs_info)
        # print(fs_info.dict)

        # fs_info_res = await mu_client.create_batch_upload_urls(req=fs_info)
        # print(fs_info_res)
        # print(fs_info_res.data)
        # print(fs_info_res.ok)
        # print(fs_info_res.task_id)
        # print(fs_info_res.batch_id)
        # print(fs_info_res.file_urls)


asyncio.run(main())
