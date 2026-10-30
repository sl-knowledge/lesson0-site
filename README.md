# 第零课 · 同一个声音，可以怎么写？

中文母语者学习日语 · 第零课试教站点。**学生版 6 页 + 教师引导支架**，纯静态、可离线、可打印。

- 线上站点：<https://sl-knowledge.github.io/lesson0-site/>
- 站点说明与开发细节：[site/README.md](site/README.md)
- 原始稿件：[日语/](日语/)（第零课 v1、第二课 v4）

## 目录

| 路径 | 内容 |
|---|---|
| `site/` | 站点工程：MkDocs 配置、内容真源、构建脚本、样式 |
| `site/content/*.yaml` | ★ 内容真源（首页 / 学生版 / 教师区） |
| `site/docs/` | 构建产物目录（Markdown 由脚本生成，勿手改） |
| `site/tools/` | YAML → Markdown 生成器、构建钩子、链接自检 |
| `日语/` | 原始稿件：学生讲义、教师引导支架、第二课 v4 |
| `.github/workflows/pages.yml` | push 到 main 后自动构建并发布到 Pages |
| `tools/package_site.py` | 打包交付件 `lesson0-site.zip`（源码 + 已构建站点） |

## 本地构建

```bash
cd site
pip install -r requirements.txt
python -m mkdocs build --strict     # 产出 _site/
python tools/check_links.py         # 站内链接自检（有断链则非零退出）
```

## 作者与许可

作者：**SL**（`SL <hiteck2019@hotmail.com>`）。

| 部分 | 许可 |
|---|---|
| 课程内容（学生讲义、文案与版面设计） | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) |
| 源代码与样式（`site/tools/`、`extra.css`、`mkdocs.yml`、CI） | MIT |
| 教师区（`site/content/teacher.yaml` 与 `日语/` 下的原始教师稿） | 保留所有权利 |

完整条款见 [LICENSE](LICENSE)。**教师区不在授权之列**：站点是纯静态页面、没有访问控制，
请勿向学生投屏教师区页面，也不要分发该链接。
