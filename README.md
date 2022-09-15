## Harbor 2.60 Python SDK 调用方法



https://github.com/goharbor/harbor 	Harbor github 地址

https://github.com/yangpeng14/harbor_sdk_v2.0  本项目基于此项目基础修改 



使用本项目发布时最新版  Harbor Version 2.60,  遭遇到无法正常调用delete相关API.

因为Harbor升级后加入了CSRF验证. 查找到比较能用的就是harbor_sdk_v2.0 , 但是无法正常获取csrf token. 



### 本项目主要功能

调用 API 接口查看 Harbor 中 repositories、tag。并提供删除方法。

### 使用举例

```python
from harbor_image import harbor

harbor.get_image_list("test_repo_name")
```
