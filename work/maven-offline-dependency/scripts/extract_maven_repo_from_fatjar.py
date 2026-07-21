#!/usr/bin/env python3
"""
从 Spring Boot fat jar 中提取所有依赖，保留 Maven 本地仓库结构。

用法:
  python3 extract_maven_repo_from_fatjar.py <fat-jar-path> [输出目录]

输出目录默认为 ./m2-repository
输出结构: {输出目录}/groupId/artifactId/version/artifactId-version.jar
"""
import zipfile
import os
import sys
import io
import re

# 强制修正: 有些 jar 内部 pom.properties 的 groupId 与 Maven 中央仓库实际坐标不一致。
# 键是 (pomPropertiesGroupId, artifactId, version)，值是正确的 groupId。
# 这个表优先级高于 pom.properties 的原始值。
FORCED_CORRECTIONS = {
    # antlr-2.7.7: pom.properties 写 org.antlr，但 Maven Central 坐标是 antlr:antlr:2.7.7
    ("org.antlr", "antlr", "2.7.7"): "antlr",
    # ant-1.9.15 / ant-launcher-1.9.15: pom.properties 写 org.apache.ant，实际是 ant:ant:1.9.15
    ("org.apache.ant", "ant", "1.9.15"): "ant",
    ("org.apache.ant", "ant-launcher", "1.9.15"): "ant",
    # stringtemplate-3.2.1: pom.properties 写 org.antlr，实际是 antlr:stringtemplate:3.2.1
    ("org.antlr", "stringtemplate", "3.2.1"): "antlr",
}

KNOWN_GROUP_IDS = {
    "activation": "javax.activation",
    "antlr": "org.antlr",
    "aopalliance": "org.aopalliance",
    "archaius-core": "com.netflix.archaius",
    "asm": "org.ow2.asm",
    "aspectjweaver": "org.aspectj",
    "bcpkix-jdk15on": "org.bouncycastle",
    "bcprov-jdk15on": "org.bouncycastle",
    "cglib": "cglib",
    "checker-qual": "org.checkerframework",
    "classmate": "com.fasterxml",
    "commons-cli": "commons-cli",
    "commons-codec": "commons-codec",
    "commons-collections4": "org.apache.commons",
    "commons-collections": "commons-collections",
    "commons-digester": "commons-digester",
    "commons-io": "commons-io",
    "commons-lang3": "org.apache.commons",
    "commons-lang": "commons-lang",
    "commons-logging": "commons-logging",
    "commons-beanutils": "commons-beanutils",
    "commons-jxpath": "commons-jxpath",
    "dom4j": "org.dom4j",
    "druid": "com.alibaba",
    "ezmorph": "net.sf.ezmorph",
    "fastjson": "com.alibaba",
    "fastjson2": "com.alibaba.fastjson2",
    "gson": "com.google.code.gson",
    "guava": "com.google.guava",
    "hibernate-validator": "org.hibernate.validator",
    "hutool-all": "cn.hutool",
    "httpclient": "org.apache.httpcomponents",
    "httpcore": "org.apache.httpcomponents",
    "jackson-annotations": "com.fasterxml.jackson.core",
    "jackson-core": "com.fasterxml.jackson.core",
    "jackson-databind": "com.fasterxml.jackson.core",
    "jackson-datatype-jsr310": "com.fasterxml.jackson.datatype",
    "jackson-module-parameter-names": "com.fasterxml.jackson.module",
    "jandex": "org.jboss",
    "javassist": "org.javassist",
    "javax.servlet-api": "javax.servlet",
    "jaxb-api": "javax.xml.bind",
    "jaxen": "jaxen",
    "jcl-over-slf4j": "org.slf4j",
    "joda-time": "joda-time",
    "json-lib": "net.sf.json-lib",
    "log4j-api": "org.apache.logging.log4j",
    "log4j-core": "org.apache.logging.log4j",
    "log4j-slf4j-impl": "org.apache.logging.log4j",
    "logback-classic": "ch.qos.logback",
    "logback-core": "ch.qos.logback",
    "lombok": "org.projectlombok",
    "mybatis": "org.mybatis",
    "mybatis-spring-boot": "org.mybatis.spring.boot",
    "mysql-connector-java": "mysql",
    "netty-all": "io.netty",
    "okhttp": "com.squareup.okhttp3",
    "okio": "com.squareup.okio",
    "poi": "org.apache.poi",
    "poi-ooxml": "org.apache.poi",
    "protobuf-java": "com.google.protobuf",
    "reflections": "org.reflections",
    "snakeyaml": "org.yaml",
    "spring-aop": "org.springframework",
    "spring-beans": "org.springframework",
    "spring-boot": "org.springframework.boot",
    "spring-boot-autoconfigure": "org.springframework.boot",
    "spring-boot-starter": "org.springframework.boot",
    "spring-boot-starter-logging": "org.springframework.boot",
    "spring-boot-starter-web": "org.springframework.boot",
    "spring-context": "org.springframework",
    "spring-core": "org.springframework",
    "spring-expression": "org.springframework",
    "spring-jcl": "org.springframework",
    "spring-web": "org.springframework",
    "spring-webmvc": "org.springframework",
    "swagger-annotations": "io.swagger",
    "swagger-models": "io.swagger",
    "validation-api": "javax.validation",
    "xercesImpl": "xerces",
    "xml-apis": "xml-apis",
    "xstream": "com.thoughtworks.xstream",
    "javax.inject": "javax.inject",
    "javax.el": "org.glassfish",
    "hibernate-core": "org.hibernate",
    "javax.persistence": "org.hibernate.javax.persistence",
    "tomcat-embed-core": "org.apache.tomcat.embed",
    "tomcat-embed-el": "org.apache.tomcat.embed",
    "tomcat-embed-websocket": "org.apache.tomcat.embed",
    "javolution": "javolution",
    "geronimo-jta_1.1_spec": "org.apache.geronimo.specs",
    "geronimo-servlet_3.0_spec": "org.apache.geronimo.specs",
    "jstl": "javax.servlet",
    "standard": "taglibs",
    "velocity": "org.apache.velocity",
    "ognl": "ognl",
    "jboss-logging": "org.jboss.logging",
    "thumbnailator": "net.coobird",
    "jsqlparser": "com.github.jsqlparser",
    "zookeeper": "org.apache.zookeeper",
    "curator-framework": "org.apache.curator",
    "curator-recipes": "org.apache.curator",
    "netty": "io.netty",
    "disruptor": "com.lmax",
    "jline": "org.jline",
    "jul-to-slf4j": "org.slf4j",
    "slf4j-api": "org.slf4j",
    "txw2": "org.glassfish.jaxb",
    "istack-commons-runtime": "com.sun.istack",
    "HikariCP": "com.zaxxer",
    "eureka-client": "com.netflix.eureka",
    "eureka-core": "com.netflix.eureka",
    "hamcrest": "org.hamcrest",
    "hamcrest-core": "org.hamcrest",
    "hystrix-core": "com.netflix.hystrix",
    "jackson-core-asl": "org.codehaus.jackson",
    "jackson-mapper-asl": "org.codehaus.jackson",
    "kafka-clients": "org.apache.kafka",
    "kotlin-stdlib": "org.jetbrains.kotlin",
    "kotlin-stdlib-common": "org.jetbrains.kotlin",
    "lz4-java": "net.jpountz.lz4",
    "mchange-commons-java": "com.mchange",
    "micrometer-core": "io.micrometer",
    "mybatis-plus": "com.baomidou",
    "mybatis-plus-annotation": "com.baomidou",
    "mybatis-plus-boot-starter": "com.baomidou",
    "mybatis-plus-core": "com.baomidou",
    "mybatis-plus-extension": "com.baomidou",
    "netflix-commons-util": "com.netflix.netflix-commons",
    "netflix-eventbus": "com.netflix.netflix-commons",
    "netflix-infix": "com.netflix.netflix-commons",
    "netflix-statistics": "com.netflix.netflix-commons",
    "poi-ooxml-schemas": "org.apache.poi",
    "reactive-streams": "org.reactivestreams",
    "reactor-core": "io.projectreactor",
    "reactor-extra": "io.projectreactor",
    "ribbon": "com.netflix.ribbon",
    "ribbon-core": "com.netflix.ribbon",
    "ribbon-eureka": "com.netflix.ribbon",
    "ribbon-httpclient": "com.netflix.ribbon",
    "ribbon-loadbalancer": "com.netflix.ribbon",
    "ribbon-transport": "com.netflix.ribbon",
    "rxjava": "io.reactivex",
    "rxnetty": "io.reactivex",
    "rxnetty-contexts": "io.reactivex",
    "rxnetty-servo": "io.reactivex",
    "servo-core": "com.netflix.servo",
    "snappy-java": "org.xerial.snappy",
    "solr-solrj": "org.apache.solr",
    "spire.doc": "com.e-iceblue",
    "spring-context-support": "org.springframework",
    "spring-jdbc": "org.springframework",
    "spring-messaging": "org.springframework",
    "spring-oxm": "org.springframework",
    "spring-tx": "org.springframework",
    "spring-boot-actuator": "org.springframework.boot",
    "spring-boot-actuator-autoconfigure": "org.springframework.boot",
    "spring-boot-starter-actuator": "org.springframework.boot",
    "spring-boot-starter-aop": "org.springframework.boot",
    "spring-boot-starter-cache": "org.springframework.boot",
    "spring-boot-starter-data-redis": "org.springframework.boot",
    "spring-boot-starter-jdbc": "org.springframework.boot",
    "spring-boot-starter-json": "org.springframework.boot",
    "spring-boot-starter-tomcat": "org.springframework.boot",
    "spring-boot-starter-validation": "org.springframework.boot",
    "spring-integration-core": "org.springframework.integration",
    "spring-integration-jmx": "org.springframework.integration",
    "spring-integration-kafka": "org.springframework.integration",
    "spring-kafka": "org.springframework.kafka",
    "spring-security-config": "org.springframework.security",
    "spring-security-core": "org.springframework.security",
    "spring-security-crypto": "org.springframework.security",
    "spring-security-web": "org.springframework.security",
    "springfox-core": "io.springfox",
    "springfox-schema": "io.springfox",
    "springfox-spi": "io.springfox",
    "springfox-spring-web": "io.springfox",
    "springfox-swagger-common": "io.springfox",
    "springfox-swagger2": "io.springfox",
    "stax-api": "javax.xml.stream",
    "xmlbeans": "org.apache.xmlbeans",
    "xmlpull": "org.xmlpull",
    "zstd-jni": "com.github.luben",
}

def get_jar_coords(jar_data: bytes) -> dict | None:
    """从 jar 内部的 pom.properties 解析 GAV 坐标"""
    try:
        inner = zipfile.ZipFile(io.BytesIO(jar_data))
        for name in inner.namelist():
            if name.endswith("/pom.properties") and name.startswith("META-INF/maven/"):
                content = inner.read(name).decode("utf-8")
                coords = {}
                for line in content.strip().split("\n"):
                    line = line.strip()
                    if "=" in line:
                        k, v = line.split("=", 1)
                        coords[k.strip()] = v.strip()
                inner.close()
                if "groupId" in coords and "artifactId" in coords and "version" in coords:
                    return coords
        inner.close()
    except Exception:
        pass
    return None

def parse_filename(jar_name: str) -> dict | None:
    """从文件名反推 artifactId + version"""
    name = jar_name.replace(".jar", "")
    m = re.search(r"-(0|[1-9]\d*)(\.(0|[1-9]\d*))*([._-](RELEASE|SNAPSHOT|Final|GA|Beta|Alpha|RC\d*))?$", name)
    if m:
        version = name[m.start()+1:]
        artifact_id = name[:m.start()]
        return {"artifactId": artifact_id, "version": version}
    return None

def extract_maven_repo(fat_jar_path: str, output_dir: str):
    print(f"📦 正在解压: {fat_jar_path}")
    z = zipfile.ZipFile(fat_jar_path)

    lib_jars = sorted([
        n for n in z.namelist()
        if n.startswith("BOOT-INF/lib/") and n.endswith(".jar")
    ])
    print(f"📎 发现 {len(lib_jars)} 个依赖 jar")

    os.makedirs(output_dir, exist_ok=True)

    success = 0
    unknown = []

    for i, jar_path in enumerate(lib_jars):
        jar_name = os.path.basename(jar_path)
        jar_data = z.read(jar_path)
        coords = get_jar_coords(jar_data)

        # 应用强制修正: 覆盖 pom.properties 中已知错误的 groupId
        if coords:
            correction_key = (coords["groupId"], coords["artifactId"], coords["version"])
            if correction_key in FORCED_CORRECTIONS:
                old_g = coords["groupId"]
                coords["groupId"] = FORCED_CORRECTIONS[correction_key]
                print(f"  ⚠️ 修正路径: {old_g}:{coords['artifactId']}:{coords['version']} → {coords['groupId']}")

        if not coords:
            parsed = parse_filename(jar_name)
            if parsed:
                g = KNOWN_GROUP_IDS.get(parsed["artifactId"], "_unknown_group")
                coords = {
                    "groupId": g,
                    "artifactId": parsed["artifactId"],
                    "version": parsed["version"],
                }
            else:
                unknown.append(jar_name)
                continue

        g = coords["groupId"].replace(".", "/")
        a = coords["artifactId"]
        v = coords["version"]
        target_dir = os.path.join(output_dir, g, a, v)
        target_file = os.path.join(target_dir, f"{a}-{v}.jar")
        os.makedirs(target_dir, exist_ok=True)
        with open(target_file, "wb") as f:
            f.write(jar_data)

        # 顺带提取 pom.xml
        try:
            inner = zipfile.ZipFile(io.BytesIO(jar_data))
            for name in inner.namelist():
                if name.endswith("/pom.xml"):
                    pom_path = os.path.join(target_dir, f"{a}-{v}.pom")
                    with open(pom_path, "wb") as pf:
                        pf.write(inner.read(name))
            inner.close()
        except Exception:
            pass

        success += 1

        if (i + 1) % 50 == 0:
            print(f"  ⏳ 进度: {i+1}/{len(lib_jars)}")

    if unknown:
        unknown_dir = os.path.join(output_dir, "_unknown")
        os.makedirs(unknown_dir, exist_ok=True)
        for jar_name in unknown:
            with open(os.path.join(unknown_dir, jar_name), "wb") as f:
                f.write(z.read(f"BOOT-INF/lib/{jar_name}"))

    z.close()

    print(f"\n✅ 完成！")
    print(f"   成功提取 (Maven结构): {success} 个")
    if unknown:
        print(f"   ⚠️ 完全无法识别: {len(unknown)} 个 (放入 _unknown/)")
        for f in unknown[:10]:
            print(f"     - {f}")
        if len(unknown) > 10:
            print(f"     ... 还有 {len(unknown)-10} 个")
    print(f"\n📁 输出目录: {os.path.abspath(output_dir)}")
    print(f"   直接拷贝到 ~/.m2/repository/ 即可使用")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 extract_maven_repo_from_fatjar.py <fat-jar.jar> [输出目录]")
        sys.exit(1)

    jar_path = sys.argv[1]
    if not os.path.isfile(jar_path):
        print(f"❌ 文件不存在: {jar_path}")
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else "./m2-repository"
    extract_maven_repo(jar_path, out_dir)
