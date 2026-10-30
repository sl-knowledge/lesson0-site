# 观察式试教站点

中文母语者学习语言的观察式试教站点：**日语四课**（第零课 → 第三课）+ **英语第一课**，每课一份学生讲义（可打印）与一份教师区页面。

- 线上：<https://sl-knowledge.github.io/lesson0-site/>
- 仓库：<https://github.com/sl-knowledge/lesson0-site>

## 目录

| 路径 | 内容 |
|---|---|
| `site/` | 站点工程：MkDocs 配置、内容真源、构建脚本、样式 |
| `site/content/*.yaml` | ★ 内容真源（首页、课程总表、各课讲义与教师页） |
| `site/docs/` | 构建目录：Markdown 由脚本生成；静态资源与讲义 PDF 在这里 |
| `site/tools/` | YAML → Markdown 生成器、讲义导入器、构建钩子、自检脚本 |
| `日语/`、`英语/` | 原始讲义稿件（教师自己的文件）：学生版 md + PDF、教师版 md + PDF |
| `.github/workflows/pages.yml` | push 到 main 后自动构建并发布到 GitHub Pages |
| `tools/package_site.py` | 打包交付件 `lesson0-site.zip`（源码 + 已构建站点） |

## 本地构建

```bash
cd site
pip install -r requirements.txt
python -m mkdocs build --strict     # 产出 _site/
python tools/check_links.py         # 站内链接自检
python tools/check_print.py         # 每个学生页是否正好一张 A4
```

## 作者与许可

作者：**SL**（`SL <hiteck2019@hotmail.com>`）。

| 部分 | 许可 |
|---|---|
| 课程内容（学生讲义、文案与版面设计） | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) |
| 源代码与样式（`site/tools/`、`extra.css`、`mkdocs.yml`、CI） | MIT |
| 教师区（教师引导与问题生成支架） | 保留所有权利 |

完整条款见 [LICENSE](LICENSE)。**教师区不在授权之列**：站点是纯静态页面、没有访问控制，
请勿向学生投屏教师区页面，也不要分发该链接。
