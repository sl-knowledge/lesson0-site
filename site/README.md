# 观察式试教站点

中文母语者学习语言的观察式试教站点：**日语四课**（第零课 → 第三课）+ **英语第一课**，每课一份学生讲义（可打印）与一份教师区页面。

- 线上：<https://sl-knowledge.github.io/lesson0-site/>
- 仓库：<https://github.com/sl-knowledge/lesson0-site>

## 技术栈

| 组件 | 版本 | 说明 |
|---|---|---|
| Python | 3.11 | 构建环境 |
| MkDocs | 1.6.1 | 站点生成 |
| Material for MkDocs | 9.8.0 | 主题 |
| PyYAML | 6.0.3 | 内容真源的格式 |

前端只有静态 HTML/CSS/JS：**没有自写 JavaScript、没有统计脚本、没有 Cookie**，`theme.font: false`（不加载 Google 字体），整站零外部请求。唯一的自定义文件是 `docs/assets/stylesheets/extra.css`。

## 目录结构

```
site/
  mkdocs.yml              站点配置与导航
  content/                ★ 内容真源（YAML）
    home.yaml             首页（课程门户）
    courses.yaml          课程与讲义总表：决定导航、门户、教师区首页
    student.yaml          第零课学生讲义（手工，对照 PDF 逐字排定）
    teacher.yaml          第零课教师页（手工）
    lessons/              其余各课的讲义与教师页（由导入器生成，可手工改）
  docs/                   构建目录：Markdown 由脚本生成，静态资源在这里
    assets/downloads/     讲义 PDF（原件副本）
    404.md                旧地址的引导页
  tools/
    build_content.py      YAML → Markdown 渲染器
    import_lessons.py     原始讲义 Markdown → 内容 YAML 的导入器
    hooks.py              构建前钩子：生成内容、同步 LICENSE
    check_links.py        站内链接自检（断链则非零退出）
    check_print.py        批量打印自检：每个学生页应正好一张 A4
    measure_overflow.py   量某个页面打印溢出了多少
    shoot.py              无头 Chrome 截图，用于人工检查版式
../日语/、../英语/         原始讲义稿件（教师自己的文件）
```

## 内容模型

YAML 用「块」描述页面，渲染器（`tools/build_content.py`）把每种块渲染成现成 HTML：

`pagehead` `para` `cards` `hero` `question` `write` `note` `admonition` `banner` `list` `table` `download` `hr` `foot` `heading` `h2` `h3` `md` `cover` `linkcard` `pagelist` `buttons` `label` `step` `hint`

- 表格与列表单元格支持 `{to: 页面.md, text: 文案}`，站内链接由渲染器按输出目录算相对 URL，不要手写路径。
- 行内标记：`**粗体**`、`*斜体*`、`` `代码` ``、`[文字](链接)`、`[[g:が]]`（彩色强调，g/a/b = 墨绿/琥珀/蓝）、`[[blank]]`（行内空白）。
- 讲义配色沿用原始 PDF：汉字墨绿、平假名蓝、片假名琥珀；底色 `#F8FBF9` / `#F2F8FB` / `#EDF6F0` / `#E2F2EB` / `#FFF9EF`。

## 加入新课程

原始讲义放在 `../日语/` 或 `../英语/`（Markdown + PDF），然后：

1. 在 `tools/import_lessons.py` 的 `SPECS` 里加一条：源文件、课名、页眉、PDF 路径。
2. `python tools/import_lessons.py` —— 生成 `content/lessons/<id>.yaml` 与 `<id>-teacher.yaml`。
3. 在 `content/courses.yaml` 里登记这一课，在 `mkdocs.yml` 的 `nav` 里补上页面。

导入器按原稿的写法自动映射组件：页标题分页、`### 标签 N｜问题` → 问题条、`**标签：** 正文` → 问题条或提示框、`**标签：** ____` → 书写区、`> 引用` → 提示框、`*提示：…*` → 灰色小字、`- [ ]` → 勾选清单、表格 → 表格、行内 `____` → 空白、`<span style="color:…">` → 彩色强调。

导入结果就是内容真源，可以直接手改；**重新导入会覆盖同名 YAML**，改过的内容请同步回原稿或导入器。

## 本地构建

```bash
cd site
pip install -r requirements.txt

python -m mkdocs build --strict     # 产出 _site/，有警告即失败
python tools/check_links.py         # 站内链接自检
python tools/check_print.py         # 每个学生页是否正好一张 A4
python -m mkdocs serve              # 本地预览
```

## 打印

每一页学生讲义在浏览器里直接打印，正好是一张 A4（与 PDF 讲义同版式）。打印样式固定使用浅色讲义配色，并压紧行距与留白；页眉、页脚、导航、翻页条在打印时隐藏。

唯一的例外是**英语第一课第 3 页**：这一页内容密度最高，原稿 PDF 是用 10.5pt 紧排才放进一张 A4，网页组件的留白放不下，浏览器打印会占两张纸——分发这一课时请用 PDF 讲义。

`python tools/check_print.py` 会批量打印所有学生页并报告超页情况；`tools/measure_overflow.py` 可以量出某个页面溢出了多少。

## 作者与许可

作者：**SL**（`SL <hiteck2019@hotmail.com>`）。

| 部分 | 许可 | 范围 |
|---|---|---|
| 课程内容 | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) | 学生讲义文案与教学设计、讲义 PDF、站点文案与版面设计 |
| 源代码与样式 | MIT | `site/tools/`、`extra.css`、`mkdocs.yml`、CI 工作流 |
| 教师区 | 保留所有权利 | `site/content/teacher.yaml`、`site/content/lessons/*-teacher.yaml` 与 `日语/`、`英语/` 下的原始教师稿 |

完整条款见仓库根目录的 `LICENSE`。仓库根目录的 `LICENSE` 是唯一真源，构建时由 `tools/hooks.py` 同步到 `docs/assets/downloads/LICENSE.txt`（该副本不进版本库）。

**教师区不在授权之列**：站点是纯静态页面、没有访问控制，**请勿向学生投屏教师区页面，也不要分发该链接**。

## 发布

`.github/workflows/pages.yml`：push 到 `main` 后自动安装依赖 → `mkdocs build --strict` → 链接自检 → 上传产物 → 部署到 GitHub Pages。构建或自检失败就不会上线。
