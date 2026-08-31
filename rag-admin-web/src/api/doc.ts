import request from './request'

export interface DocItem {
  id: number
  filename: string
  file_type: string
  tag: string
  preview: string
  upload_time: string
  uploader_id: number
  chunk_count: number
  parse_status: string
}

// 文档列表：GET /api/doc/list
export function listDocApi(): Promise<DocItem[]> {
  return request({ url: '/doc/list', method: 'get' })
}

// 上传文档：POST /api/doc/upload (multipart/form-data)
export function uploadDocApi(file: File, tag = '') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('tag', tag)
  return request({
    url: '/doc/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 删除文档：DELETE /api/doc/{id}
export function deleteDocApi(id: number) {
  return request({ url: `/doc/${id}`, method: 'delete' })
}