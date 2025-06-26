# 模板重构说明

## 概述

为了减少代码重复和提高维护性，我们将左侧菜单栏提取为公共部分，创建了基于Jinja2模板继承的模块化系统。

## 文件结构

```
templates/
├── base.html                    # 基础布局模板
├── includes/                    # 公共组件目录
│   ├── navbar.html             # 顶部导航栏
│   ├── sidebar.html            # 左侧菜单栏
│   └── sidebar_styles.html     # 侧边栏样式
├── index.html                  # 知识库管理页面
├── text_blocks.html            # 文本块查询页面
├── user_management.html        # 用户管理页面
├── permission_management.html  # 权限管理页面
└── prompt_management.html      # 提示词管理页面
```

## 核心组件

### 1. 基础布局模板 (`base.html`)

包含所有页面的公共结构：
- HTML文档基础结构
- 公共CSS和JavaScript引用
- 导航栏和侧边栏引用
- 内容区域占位符

### 2. 公共组件

#### 导航栏 (`includes/navbar.html`)
- 顶部导航栏
- 用户信息显示
- 退出登录功能

#### 侧边栏 (`includes/sidebar.html`)
- 左侧菜单导航
- 动态高亮当前页面
- 权限控制（管理员菜单）

#### 侧边栏样式 (`includes/sidebar_styles.html`)
- 统一的侧边栏样式
- 响应式设计
- 一致的视觉效果

## 使用方法

### 创建新页面

1. **继承基础模板**：
```html
{% extends "base.html" %}
```

2. **设置页面标题**：
```html
{% block title %}页面标题 - 本地知识库管理{% endblock %}
```

3. **添加页面特定样式**：
```html
{% block extra_styles %}
<style>
    /* 页面特定样式 */
</style>
{% endblock %}
```

4. **添加页面内容**：
```html
{% block content %}
<!-- 页面主要内容 -->
{% endblock %}
```

5. **添加页面特定脚本**：
```html
{% block extra_scripts %}
<script>
    // 页面特定JavaScript
</script>
{% endblock %}
```

### 示例：新页面模板

```html
{% extends "base.html" %}

{% block title %}新功能页面 - 本地知识库管理{% endblock %}

{% block extra_styles %}
<style>
    .custom-style {
        /* 自定义样式 */
    }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5>新功能</h5>
                </div>
                <div class="card-body">
                    <!-- 页面内容 -->
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
    // 页面特定JavaScript代码
</script>
{% endblock %}
```

## 优势

### 1. **代码复用**
- 导航栏和侧边栏只需维护一份代码
- 样式和布局保持一致

### 2. **易于维护**
- 修改公共部分只需更新一个文件
- 新增页面不需要重复编写公共代码

### 3. **权限控制**
- 侧边栏自动根据用户权限显示菜单项
- 管理员功能自动隐藏/显示

### 4. **响应式设计**
- 统一的移动端适配
- 一致的用户体验

## 注意事项

### 1. **保持一致性**
- 新页面应遵循现有的样式规范
- 使用相同的Bootstrap组件和图标

### 2. **权限控制**
- 管理员功能使用 `{% if current_user.is_admin %}` 条件
- 确保权限检查正确

### 3. **路由名称**
- 确保侧边栏中的路由名称与Flask路由一致
- 使用 `url_for()` 函数生成链接

### 4. **样式隔离**
- 页面特定样式放在 `extra_styles` 块中
- 避免与公共样式冲突

## 迁移指南

### 从旧模板迁移

1. **替换HTML结构**：
   - 移除 `<!DOCTYPE html>` 到 `</body>` 的完整HTML结构
   - 添加 `{% extends "base.html" %}`

2. **提取页面特定样式**：
   - 将页面特定的CSS移到 `{% block extra_styles %}` 块中
   - 移除公共样式（导航栏、侧边栏等）

3. **提取页面内容**：
   - 将主要内容移到 `{% block content %}` 块中
   - 移除导航栏和侧边栏HTML

4. **提取页面脚本**：
   - 将页面特定的JavaScript移到 `{% block extra_scripts %}` 块中
   - 移除公共脚本引用

### 验证迁移

1. **功能测试**：
   - 确保所有功能正常工作
   - 检查导航和权限控制

2. **样式检查**：
   - 确保页面样式正确显示
   - 检查响应式设计

3. **浏览器兼容性**：
   - 测试不同浏览器的兼容性
   - 确保JavaScript功能正常

## 故障排除

### 常见问题

1. **模板继承错误**：
   - 检查 `base.html` 文件路径
   - 确保Jinja2语法正确

2. **样式冲突**：
   - 检查CSS选择器优先级
   - 使用更具体的选择器

3. **JavaScript错误**：
   - 检查脚本加载顺序
   - 确保依赖库正确加载

4. **权限问题**：
   - 检查用户权限设置
   - 验证条件判断逻辑

## 扩展指南

### 添加新的公共组件

1. 在 `includes/` 目录下创建新文件
2. 在 `base.html` 中引用新组件
3. 更新相关文档

### 修改公共样式

1. 更新 `includes/sidebar_styles.html`
2. 测试所有页面的显示效果
3. 确保响应式设计正常

### 添加新的菜单项

1. 更新 `includes/sidebar.html`
2. 添加相应的Flask路由
3. 更新权限控制逻辑 