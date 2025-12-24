import asyncio
from aclient import *

TEST_CREATE_TASK_FROM_URL = True
# TEST_CREATE_TASK_FROM_URL = False

TEST_GET_TASK = True
# TEST_GET_TASK = False

async def test_create_task_from_url(mu_client):
    print('TEST: 从URL创建单个文件解析任务 ...')
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
    print(f'测试 [{urls[0]}] 通过！task_id={res.task_id}')
    # Response(code=0, msg='ok', data={'task_id': 'b4800fe7-9e7a-49af-97f8-560f7c6fb2e3'}, trace_id='b25ea889a35ca335970f1f9c9ae6c558')


    print(f'测试 [{urls[1]}] ...')
    res = await mu_client.create_task_from_url(url=urls[1])
    print(res)
    # Response(code=0, msg='ok', data={'task_id': 'c11d9fa5-69d0-46f9-94d9-30d0e9602962'}, trace_id='b07ad4177396dd9889e2535dd155461c')
    print(f'测试 [{urls[1]}] 通过！task_id={res.task_id}')

    print('Success! TEST: 从URL创建单个文件解析任务')
    return res.task_id

async def test_get_task(mu_client, task_id):
    print('TEST: 获取任务详情 ...')
    task_info = await mu_client.get_task(task_id[0])
    print(task_info)
    # TaskInfo(task_id='f9a9aec8-aa91-4264-b8a7-32f249be6fad', status='done', err_msg='', extract_progress=None, full_zip_url='https://cdn-mineru.openxlab.org.cn/pdf/2025-12-24/c11d9fa5-69d0-46f9-94d9-30d0e9602962.zip', model_version='pipeline2.6.5')
    print('Success! TEST: 获取任务详情')

async def main():
    async with AsyncMinerUClient() as mu_client:
        # TEST: 从URL创建单个文件解析任务
        if TEST_CREATE_TASK_FROM_URL:
            task_id = await test_create_task_from_url(mu_client)
        else:
            task_id = ['b4800fe7-9e7a-49af-97f8-560f7c6fb2e3', 'c11d9fa5-69d0-46f9-94d9-30d0e9602962']

        # TEST: 获取任务详情
        if TEST_GET_TASK:await test_get_task(mu_client, task_id)


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
