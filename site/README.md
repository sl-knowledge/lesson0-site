# 第零课站点 · 同一个声音，可以怎么写？

中文母语者学习日语 · 第零课试教站点。学生版 6 页 + 教师引导支架。

## 技术栈

| 层 | 用的什么 |
|---|---|
| 站点生成 | MkDocs 1.6.1 + Material for MkDocs 9.8.0（Python 3.11） |
| 内容格式 | Markdown（`.md`） |
| 内容真源 | YAML（PyYAML 6.0.3） |
| 前端 | 纯静态 HTML/CSS/JS，无自写 JS、无统计、无 cookie |
| 产出 | `python -m mkdocs build --strict` → `_site/` 静态文件 |

除 Material 主题自带的搜索与翻页功能外，没有任何自写 JavaScript；没有统计脚本，没有 Cookie，
`theme.font: false` 关闭了 Google 字体，站点不向外部站点发起任何请求。

## 快速开始

```bash
pip install -r requirements.txt
python -m mkdocs build --strict     # 产出 _site/
python -m mkdocs serve              # 本地预览 http://127.0.0.1:8000
python tools/check_links.py         # 站内链接自检（有断链则非零退出）
```

## 目录结构

```
site/
├─ mkdocs.yml                 站点配置（导航、主题、隐私相关开关）
├─ requirements.txt           版本锁定
├─ content/                   ★ 内容真源（YAML）
│  ├─ home.yaml               首页
│  ├─ student.yaml            学生版：概览 + 6 页
│  └─ teacher.yaml            教师区：引导支架与核查
├─ tools/
│  ├─ build_content.py        YAML → Markdown 生成器
│  ├─ hooks.py                mkdocs pre_build 钩子
│  └─ check_links.py          站内链接自检
└─ docs/
   ├─ assets/stylesheets/extra.css   唯一的自定义样式表
   ├─ assets/downloads/              学生版 PDF（A4 六页）
   └─ *.md                           ← 自动生成，勿手改
```

## 内容怎么改

**只改 `content/*.yaml`，不要手改 `docs/` 里的 Markdown**（那些是构建产物）。
改完跑一次 `python -m mkdocs build --strict` 即可；`pre_build` 钩子会在构建前自动重新渲染。

`content/student.yaml` 里每一页由若干内容块组成，块类型在 `tools/build_content.py` 中定义：

| 块类型 | 作用 |
|---|---|
| `pagehead` | 讲义页眉（课题 + 页码） |
| `para` | 段落；`lead: true` 为导语 |
| `cards` | 卡片组；卡片可分色（`accent`）或逐字分色（`parts`） |
| `hero` | 居中大字卡片（罗马字 / きしゃ） |
| `question` | 问题条：编号 + 标签（观察 / 问题 / 比较 …） |
| `write` | 书写区；`box: true` 为虚线框，`lines` 为横线条数 |
| `note` | 提示框；`tone: amber` 为琥珀色 |
| `heading` | 二级 / 三级标题（进入右侧目录） |
| `list` | 列表；`marker: checkbox` 为观察清单 |
| `table` | 表格；单元格可写 `{to: 页面.md, text: 文案}` 自动生成站内链接 |
| `download` | 可下载文件提示块（打印版 PDF） |
| `hr` / `foot` | 分隔线 / 页脚小字 |

站内链接不要手写路径：用 `{to: student/page-3.md}`，生成器会按页面在 `_site` 中的实际位置算出相对 URL。

## 字体是怎么定的

站点**不加载任何网络字体**（`theme.font: false`），全部用系统字体，靠字体栈的**回退顺序**来分工：

```css
/* 正文：拉丁字统一走 Segoe UI，中文落到微软雅黑 */
--l0-sans: system-ui, -apple-system, "Segoe UI", "PingFang SC", "Hiragino Sans GB",
  "Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC", "Source Han Sans SC", sans-serif;

/* 例词：拉丁字同样走 Segoe UI，汉字假名落到日文黑体（游ゴシック / Noto Sans JP） */
--l0-jp: "Segoe UI", system-ui, "Yu Gothic UI", "Yu Gothic", "Hiragino Sans",
  "Noto Sans JP", "Meiryo", "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", sans-serif;
```

要点：

- **拉丁字必须放在栈的最前面**。浏览器逐字符回退，Segoe UI 没有汉字，汉字才会落到后面的雅黑／游ゴシック；
  如果把 `serif` 放在末尾，拉丁字会掉进 Times New Roman，页面上就会出现三张脸、大小不一。
- **例词用日文黑体**（游ゴシック / Noto Sans JP），日文字形（べ・いぬ・きゃ）才是对的；
  微软雅黑里的假名是中式字形。
- 想换别的字体时，先用 `design/font-probe.html` 对比一下实际渲染效果（里面列了几组候选字体的并排样张）。

## 两处需要留意的设计决定

1. **学生版与教师版分开。** 学生页只呈现材料与问题；预设路径、逐级提示、示范答案全部在独立的
   「教师区」页面。教师区页面顶部有醒目横幅提示。
2. **教师区没有访问控制。** 站点是纯静态页面，任何知道 URL 的人都能打开 `teacher/guide/`。
   上课时请勿投屏该页，也不要把该链接发给学生；需要真正的权限隔离时，请在部署层加保护。

## 作者与许可

作者：**SL**（`SL <hiteck2019@hotmail.com>`）。

| 部分 | 许可 | 范围 |
|---|---|---|
| 课程内容 | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) | 学生讲义文案与教学设计、讲义 PDF、站点文案与版面设计 |
| 源代码与样式 | MIT | `site/tools/`、`extra.css`、`mkdocs.yml`、CI 工作流 |
| 教师区 | 保留所有权利 | `site/content/teacher.yaml` 与 `日语/` 下的原始教师稿 |

- CC BY-NC-SA 4.0：可分享、可改编，需署名 SL、说明改动、限于非商业用途，衍生作品须以同一协议发布。
- 仓库根目录的 `LICENSE` 是唯一真源。构建时 `tools/hooks.py` 会把它同步到
  `site/docs/assets/downloads/LICENSE.txt`（该副本不进版本库），站内公布的协议因此与仓库里的那份始终一致。
- 教师区不在授权之列：站点是纯静态页面、没有访问控制，**请勿向学生投屏或分发该链接**。

## 打印

每一页都按 A4 讲义排版，浏览器直接打印（Ctrl/Cmd + P）即可当作讲义分发；
站点内也提供了与 PDF 讲义一致的可下载版本。
