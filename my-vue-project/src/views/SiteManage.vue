<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const searchQuery = ref('')

const tableData = ref([
  { id: 'ST-001', name: '朝阳区奥体中心站', location: '北京市朝阳区', status: '正常' },
  { id: 'ST-002', name: '海淀区万柳站', location: '北京市海淀区', status: '告警' },
  { id: 'ST-003', name: '东城区天坛站', location: '北京市东城区', status: '正常' },
  { id: 'ST-004', name: '西城区万寿西宫站', location: '北京市西城区', status: '离线' },
])

const dialogVisible = ref(false)
const isEdit = ref(false)

// 【第一步】：获取表单组件的引用（为了最后能喊它执行检查）
const formRef = ref(null)

const siteForm = reactive({
  name: '',
  location: '',
  status: '正常',
})

// 【第二步】：定义校验规则
const siteRules = reactive({
  name: [
    { required: true, message: '站点名称不能为空', trigger: 'blur' }, // trigger: 'blur' 意思是鼠标失去焦点时触发校验
    { min: 3, max: 20, message: '站点名称长度必须在 3 到 20 个字符之间', trigger: 'blur' },
  ],
  location: [{ required: true, message: '地理位置不能为空', trigger: 'blur' }],
  // status 因为是下拉框，且给了默认值，通常不需要必填校验
})

const handleAdd = () => {
  isEdit.value = false
  Object.assign(siteForm, { name: '', location: '', status: '正常' })
  dialogVisible.value = true

  // 打开弹窗时，清除上一次可能残留的爆红校验提示
  setTimeout(() => {
    if (formRef.value) formRef.value.clearValidate()
  }, 0)
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(siteForm, { name: row.name, location: row.location, status: row.status })
  dialogVisible.value = true
}

const handleSubmit = () => {
  // 防御性编程：确保表单已经渲染出来了
  if (!formRef.value) return

  // 【第三步】：调用 validate 方法进行全面体检
  formRef.value.validate((valid) => {
    if (valid) {
      // 校验全票通过！执行保存逻辑
      dialogVisible.value = false
      ElMessage.success(isEdit.value ? '修改保存成功！' : '新增站点成功！')
    } else {
      // 校验没通过，阻止提交并提示用户
      ElMessage.error('请检查表单填写是否有误，带红星的为必填项！')
      return false
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要永久删除站点 "${row.name}" 吗？`, '删除警告', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      ElMessage.success('站点已删除')
    })
    .catch(() => {
      ElMessage.info('已取消删除')
    })
}
</script>

<template>
  <div class="site-manage-container">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-button type="primary" @click="handleAdd">➕ 新增站点</el-button>
        <div class="search-box">
          <el-input
            v-model="searchQuery"
            placeholder="请输入站点名称"
            clearable
            style="width: 250px; margin-right: 10px"
          />
          <el-button>搜索</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="table-card">
      <el-table :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="id" label="站点编号" width="120" />
        <el-table-column prop="name" label="站点名称" min-width="180" />
        <el-table-column prop="location" label="地理位置" min-width="180" />
        <el-table-column prop="status" label="运行状态" width="120">
          <template #default="scope">
            <el-tag
              :type="
                scope.row.status === '正常'
                  ? 'success'
                  : scope.row.status === '告警'
                    ? 'danger'
                    : 'info'
              "
            >
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(scope.row)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          background
          layout="total, prev, pager, next, jumper"
          :total="42"
          :page-size="10"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑站点信息' : '新增监测站点'"
      width="500px"
    >
      <el-form ref="formRef" :model="siteForm" :rules="siteRules" label-width="80px">
        <el-form-item label="站点名称" prop="name">
          <el-input v-model="siteForm.name" placeholder="请输入名称，例如：朝阳区测试站"></el-input>
        </el-form-item>

        <el-form-item label="地理位置" prop="location">
          <el-input v-model="siteForm.location" placeholder="请输入详细地址"></el-input>
        </el-form-item>

        <el-form-item label="运行状态" prop="status">
          <el-select v-model="siteForm.status" style="width: 100%">
            <el-option label="正常" value="正常" />
            <el-option label="告警" value="告警" />
            <el-option label="离线" value="离线" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">保存配置</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.site-manage-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.search-box {
  display: flex;
}
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
