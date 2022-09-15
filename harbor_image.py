# !/usr/bin/python3
# -*- coding=utf8 -*-
import base64
import inspect
import logging
import requests

method_map = {"get": requests.get,
              "post": requests.post,
              "put": requests.put,
              "head": requests.head,
              "delete": requests.delete}


def handle_error(e, func_name):
    logging.error(f"############# Exception: {func_name} #############")
    logging.error(e)
    logging.error(e.__traceback__.tb_frame.f_globals["__file__"])
    logging.error(e.__traceback__.tb_lineno)


class Harbor:
    def __init__(self):
        self.host = "http://host:ip"
        self.user = "admin"
        self.password = "Harbor12345"
        self.harbor_project_name = "项目名称"

        # 第一次get请求，获取 cookie 信息
        self.cookies, self.headers = self.get_cookie()

        # 获取登陆成功 session
        self.session_id = self.login()

        # 把登陆成功的 sid值 替换 get_cookie 方法中 cookie sid值，用于 delete 操作
        self.cookies_new = self.cookies
        self.cookies_new.update({"sid": self.session_id})

    def get_cookie(self):
        """ 第一次拿到token 及 csrf_token """
        response = requests.post("{}/c/login".format(self.host))
        csrf_cookie = response.cookies.get_dict()
        csrf_token = response.headers.get("X-Harbor-CSRF-Token")
        authorization = base64.encodebytes(f"{self.user}:{self.password}".encode()).decode().strip()
        headers = {"accept": "application/json",
                   "authorization": f"Basic {authorization}",
                   "X-Harbor-CSRF-Token": csrf_token}
        return csrf_cookie, headers

    def login(self):
        """ 第一次登陆 获取身份及 cookie中的 sid 更新 cookie 不然无法调用删除功能 """
        login_data = requests.post("{}/c/login".format(self.host),
                                   data={"principal": self.user, "password": self.password},
                                   cookies=self.cookies, headers=self.headers)

        if login_data.status_code == 200:
            session_id = login_data.cookies.get("sid")

            logging.debug("Harbor: successfully login, session id: {}.".format(session_id))
            return session_id

        logging.error("Harbor: fail to login, please try again.")

    def gen_response(self, method="get", link_params=""):
        """ 请求做了封装 统一使用获取的header及cookie """
        host = self.host + link_params
        resp = method_map[method](host, headers=self.headers, cookies=self.cookies_new)  # type: requests.Response
        return resp

    def get_repo_list(self):
        """ 获取项目下的仓库 """
        logging.debug("working on tenant Harbor get_repo_list")
        try:
            res = []
            page_size = 20
            link_params = "/api/v2.0/projects/{}/repositories?page={}&page_size={}"
            repo_data = self.gen_response(link_params=link_params.format(self.harbor_project_name, 1, page_size))
            total_count = repo_data.headers["x-total-count"]
            res_tmp = [i["name"].split("/")[-1] for i in repo_data.json()]
            res.extend(res_tmp)
            current_page = 2
            while len(res) < int(total_count):
                link_params_new = link_params.format(self.harbor_project_name, current_page, page_size)
                result = self.gen_response(link_params=link_params_new)
                res_tmp = [i["name"].split("/")[-1] for i in result.json()]
                if res_tmp:
                    res.extend(res_tmp)
                current_page += 1
            return res
        except Exception as e:
            handle_error(e, inspect.stack()[0][3])

    def delete_repo(self, repo_name):
        """ 删除仓库 """
        logging.debug("working on tenant Harbor delete_repo")
        try:
            if repo_name not in self.get_repo_list():
                return True
            link_params = "/api/v2.0/projects/{}/repositories/{}".format(self.harbor_project_name, repo_name)
            delete_data = self.gen_response("delete", link_params=link_params)
            if delete_data.status_code == 200 and repo_name not in self.get_repo_list():
                return True
            return False
        except Exception as e:
            handle_error(e, inspect.stack()[0][3])

    def get_image_list(self, repo_name):
        """ 获取镜像列表(tag) """
        logging.debug("working on tenant Harbor get_image_list")
        try:
            res = []
            page_size = 2
            link_params = "/api/v2.0/projects/{}/repositories/{}/artifacts?page={}&page_size={}"
            params = link_params.format(self.harbor_project_name, repo_name, 1, page_size)
            image_data = self.gen_response(link_params=params)
            total_count = image_data.headers["x-total-count"]
            res_tmp = [i["tags"][0]["name"] for i in image_data.json()]
            res.extend(res_tmp)
            current_page = 2
            while len(res) < int(total_count):
                link_params_new = link_params.format(self.harbor_project_name, repo_name, current_page, page_size)
                result = self.gen_response(link_params=link_params_new)
                res_tmp = [i["tags"][0]["name"] for i in result.json()]
                if res_tmp:
                    res.extend(res_tmp)
                current_page += 1
            return res
        except Exception as e:
            handle_error(e, inspect.stack()[0][3])

    def delete_image(self, repo_name, image_tag):
        """ 通过tag删除镜像 """
        logging.debug("working on tenant Harbor delete_image")
        try:
            if image_tag not in self.get_image_list(repo_name):
                return True
            link_params = "/api/v2.0/projects/{}/repositories/{}/artifacts/{}"
            params = link_params.format(self.harbor_project_name, repo_name, image_tag)
            delete_data = self.gen_response("delete", link_params=params)
            if delete_data.status_code == 200 and image_tag not in self.get_image_list(repo_name):
                return True
        except Exception as e:
            handle_error(e, inspect.stack()[0][3])


harbor = Harbor()
if __name__ == '__main__':
    print(harbor.get_image_list("repo_nane"))
