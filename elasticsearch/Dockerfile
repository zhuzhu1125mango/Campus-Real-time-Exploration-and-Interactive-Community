FROM elasticsearch:8.14.3

# 安装中文 IK 分词插件
# 插件版本需与 ES 版本匹配，详见 https://github.com/infinilabs/analysis-ik
# 国内网络建议使用 release.infinilabs.com 官方发布站
RUN bin/elasticsearch-plugin install --batch https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-8.14.3.zip
