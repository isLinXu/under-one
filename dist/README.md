# dist/

本目录用于存放 UnderOne 的**构建产物（build artifacts）**；`.skill` 分发包不被 git 追踪。

- `*.skill` · 由 `underone/scripts/build_skill_bundles.py` 从各 skill 子目录打包生成
- 需要重新生成时执行 `make bundles`；如果已经 `pip install -e underone/`，也可以执行 `under-one bundles`
- GitHub Release 会在 `package` job 中自动构建并上传为 release assets

## 为什么不进 git

1. 源码已在 `underone/skills/{skill}/`，`.skill` 是衍生产物
2. 每次源码变更都要重新打包，否则产物过时，会造成 git diff 噪声
3. 分发包适合放 release assets，而不是作为常规源码差异提交

## 如何使用

```bash
# 从源码构建
make bundles                     # → 本目录产出 10 个 .skill

# 或从 GitHub Release 下载预构建版本
curl -L -o bagua-zhen.skill \
  https://github.com/<user>/under-one/releases/latest/download/bagua-zhen.skill
```
