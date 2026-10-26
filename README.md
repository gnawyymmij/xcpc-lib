# XCPC 算法模板

按原模板目录整理的算法竞赛资料，保留原目录层级和阅读顺序，并修复算法实现及多测状态管理问题。共六大类、56 个独立算法／专题 `.tex` 文件。

- [总入口：模板.tex](%E6%A8%A1%E6%9D%BF.tex)：组织各级标题，通过 `\input` 引入算法文件。
- [当前修订版 PDF](%E6%A8%A1%E6%9D%BF.pdf)：由当前拆分源码编译，包含多测与使用条件。
- `01-` 到 `06-` 文件夹对应原目录的六大类；下级分类继续建文件夹，最底层为单个算法／专题文件。数字前缀对应原目录顺序；文件名中的 `/` 替换为 `／`。

## 编译

安装包含 `ctex`、`listings`、`hyperref` 的 TeX Live 或 MiKTeX，在仓库根目录执行：

```sh
latexmk 模板.tex
```

配置默认使用 XeLaTeX，生成 `build/模板.pdf`。也可手动运行两次：

```sh
xelatex -interaction=nonstopmode -halt-on-error 模板.tex
xelatex -interaction=nonstopmode -halt-on-error 模板.tex
```

修改算法时直接编辑对应 `.tex` 文件，再编译总入口。算法文件是文档片段，不单独编译。原稿使用 `\date{\today}`，重新编译时封面日期会更新。

多项式已统一为 vector 接口（NTT、求逆、对数、指数、幂、除法）；Bostan–Mori 为同级独立文件。部分修复涉及接口变化，特别是后缀数组使用 0 下标、多项式精度表示保留项数，详见相应条目。

## 正确性、多测与回归

全部 56 个条目均已逐项审查，44 组提取源码的回归测试已通过。每个条目说明初始化／清空方法及适用条件，具体问题与验证范围见 [审计记录](AUDIT.md)。保留数组的旧片段仍需提供自己的快读和竞赛宏；统一使用 GNU C++17，多个同名片段请隔离作用域。

回归脚本直接提取 TeX 中的代码并进行编译、随机对拍和连续多测：

```sh
python tests/test_templates.py
```

需要 Python 与 `g++`；运行输出保存在忽略的 `build/tests/`。未把公式核对、概率哈希及依题目约束的条件表述为全输入运行验证。

## 算法目录

- **1 数据结构 (Data Structures)**
  - [1.1 哈希表](01-%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84/01-%E5%93%88%E5%B8%8C%E8%A1%A8.tex)
  - [1.2 fhq-treap](01-%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84/02-fhq-treap.tex)
  - [1.3 RMQ (ST 表)](01-%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84/03-RMQ.tex)
  - [1.4 笛卡尔树 (Cartesian Tree)](01-%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84/04-%E7%AC%9B%E5%8D%A1%E5%B0%94%E6%A0%91.tex)
  - [1.5 树链剖分 (Heavy-Light Decomposition)](01-%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84/05-%E6%A0%91%E9%93%BE%E5%89%96%E5%88%86.tex)
  - [1.6 LCT (Link-Cut Tree)](01-%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84/06-LCT.tex)
  - [1.7 李超线段树](01-%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84/07-%E6%9D%8E%E8%B6%85%E7%BA%BF%E6%AE%B5%E6%A0%91.tex)
- **2 图论 (Graph Theory)**
  - **2.1 连通性 (Connectivity)**
    - [2.1.1 Tarjan 求 SCC (Strongly Connected Components)](02-%E5%9B%BE%E8%AE%BA/01-%E8%BF%9E%E9%80%9A%E6%80%A7/01-Tarjan%20%E6%B1%82%20SCC.tex)
    - [2.1.2 仅加边动态 scc](02-%E5%9B%BE%E8%AE%BA/01-%E8%BF%9E%E9%80%9A%E6%80%A7/02-%E4%BB%85%E5%8A%A0%E8%BE%B9%E5%8A%A8%E6%80%81%20scc.tex)
    - [2.1.3 点双 / 边双 (Biconnected Components)](02-%E5%9B%BE%E8%AE%BA/01-%E8%BF%9E%E9%80%9A%E6%80%A7/03-%E7%82%B9%E5%8F%8C%20%EF%BC%8F%20%E8%BE%B9%E5%8F%8C.tex)
    - [2.1.4 圆方树 (Round-Square Tree)](02-%E5%9B%BE%E8%AE%BA/01-%E8%BF%9E%E9%80%9A%E6%80%A7/04-%E5%9C%86%E6%96%B9%E6%A0%91.tex)
  - **2.2 最短路 (Shortest Path)**
    - [2.2.1 负环 (Negative Cycle Detection - SPFA)](02-%E5%9B%BE%E8%AE%BA/02-%E6%9C%80%E7%9F%AD%E8%B7%AF/01-%E8%B4%9F%E7%8E%AF.tex)
  - [2.3 欧拉路径 (Eulerian Path)](02-%E5%9B%BE%E8%AE%BA/03-%E6%AC%A7%E6%8B%89%E8%B7%AF%E5%BE%84.tex)
  - **2.4 网络流 (Network Flow)**
    - [2.4.1 Dinic (Max Flow)](02-%E5%9B%BE%E8%AE%BA/04-%E7%BD%91%E7%BB%9C%E6%B5%81/01-Dinic.tex)
    - [2.4.2 MCMF (Min Cost Max Flow)](02-%E5%9B%BE%E8%AE%BA/04-%E7%BD%91%E7%BB%9C%E6%B5%81/02-MCMF.tex)
    - [2.4.3 网络流经典模型](02-%E5%9B%BE%E8%AE%BA/04-%E7%BD%91%E7%BB%9C%E6%B5%81/03-%E7%BD%91%E7%BB%9C%E6%B5%81%E7%BB%8F%E5%85%B8%E6%A8%A1%E5%9E%8B.tex)
  - **2.5 图匹配 (Graph Matching)**
    - [2.5.1 二分图最小权完美匹配 (KM / SSP)](02-%E5%9B%BE%E8%AE%BA/05-%E5%9B%BE%E5%8C%B9%E9%85%8D/01-%E4%BA%8C%E5%88%86%E5%9B%BE%E6%9C%80%E5%B0%8F%E6%9D%83%E5%AE%8C%E7%BE%8E%E5%8C%B9%E9%85%8D.tex)
  - **2.6 树上算法 (Tree Algorithms)**
    - [2.6.1 树的重心 (Tree Centroid)](02-%E5%9B%BE%E8%AE%BA/06-%E6%A0%91%E4%B8%8A%E7%AE%97%E6%B3%95/01-%E6%A0%91%E7%9A%84%E9%87%8D%E5%BF%83.tex)
    - [2.6.2 树上离某个点最远的点](02-%E5%9B%BE%E8%AE%BA/06-%E6%A0%91%E4%B8%8A%E7%AE%97%E6%B3%95/02-%E6%A0%91%E4%B8%8A%E7%A6%BB%E6%9F%90%E4%B8%AA%E7%82%B9%E6%9C%80%E8%BF%9C%E7%9A%84%E7%82%B9.tex)
    - [2.6.3 斯坦纳树 (Steiner Tree)](02-%E5%9B%BE%E8%AE%BA/06-%E6%A0%91%E4%B8%8A%E7%AE%97%E6%B3%95/03-%E6%96%AF%E5%9D%A6%E7%BA%B3%E6%A0%91.tex)
  - [2.7 2-SAT](02-%E5%9B%BE%E8%AE%BA/07-2-SAT.tex)
- **3 动态规划 (Dynamic Programming)**
  - [3.1 WQS 二分](03-%E5%8A%A8%E6%80%81%E8%A7%84%E5%88%92/01-WQS%20%E4%BA%8C%E5%88%86.tex)
  - [3.2 决策单调性与二分队列](03-%E5%8A%A8%E6%80%81%E8%A7%84%E5%88%92/02-%E5%86%B3%E7%AD%96%E5%8D%95%E8%B0%83%E6%80%A7%E4%B8%8E%E4%BA%8C%E5%88%86%E9%98%9F%E5%88%97.tex)
- **4 字符串 (String Algorithms)**
  - [4.1 字符串哈希 (String Hashing)](04-%E5%AD%97%E7%AC%A6%E4%B8%B2/01-%E5%AD%97%E7%AC%A6%E4%B8%B2%E5%93%88%E5%B8%8C.tex)
  - [4.2 KMP](04-%E5%AD%97%E7%AC%A6%E4%B8%B2/02-KMP.tex)
  - [4.3 Manacher](04-%E5%AD%97%E7%AC%A6%E4%B8%B2/03-Manacher.tex)
  - [4.4 AC 自动机 (Aho-Corasick)](04-%E5%AD%97%E7%AC%A6%E4%B8%B2/04-AC%20%E8%87%AA%E5%8A%A8%E6%9C%BA.tex)
  - [4.5 后缀数组 (Suffix Array - SA)](04-%E5%AD%97%E7%AC%A6%E4%B8%B2/05-%E5%90%8E%E7%BC%80%E6%95%B0%E7%BB%84.tex)
  - [4.6 回文自动机 (Palindrome Automaton - PAM)](04-%E5%AD%97%E7%AC%A6%E4%B8%B2/06-%E5%9B%9E%E6%96%87%E8%87%AA%E5%8A%A8%E6%9C%BA.tex)
- **5 数学 (Mathematics)**
  - **5.1 数论 (Number Theory)**
    - [5.1.1 Exgcd (Extended Euclidean Algorithm)](05-%E6%95%B0%E5%AD%A6/01-%E6%95%B0%E8%AE%BA/01-Exgcd.tex)
    - [5.1.2 万能欧几里得](05-%E6%95%B0%E5%AD%A6/01-%E6%95%B0%E8%AE%BA/02-%E4%B8%87%E8%83%BD%E6%AC%A7%E5%87%A0%E9%87%8C%E5%BE%97.tex)
    - [5.1.3 ExCRT (Extended Chinese Remainder Theorem)](05-%E6%95%B0%E5%AD%A6/01-%E6%95%B0%E8%AE%BA/03-ExCRT.tex)
    - [5.1.4 扩展欧拉定理 (Euler's Totient Theorem)](05-%E6%95%B0%E5%AD%A6/01-%E6%95%B0%E8%AE%BA/04-%E6%89%A9%E5%B1%95%E6%AC%A7%E6%8B%89%E5%AE%9A%E7%90%86.tex)
    - [5.1.5 Pollard-Rho](05-%E6%95%B0%E5%AD%A6/01-%E6%95%B0%E8%AE%BA/05-Pollard-Rho.tex)
    - [5.1.6 Dirichlet 前缀和 (Dirichlet Prefix Sum)](05-%E6%95%B0%E5%AD%A6/01-%E6%95%B0%E8%AE%BA/06-Dirichlet%20%E5%89%8D%E7%BC%80%E5%92%8C.tex)
    - [5.1.7 杜教筛 (Du's Sieve)](05-%E6%95%B0%E5%AD%A6/01-%E6%95%B0%E8%AE%BA/07-%E6%9D%9C%E6%95%99%E7%AD%9B.tex)
    - [5.1.8 Min25](05-%E6%95%B0%E5%AD%A6/01-%E6%95%B0%E8%AE%BA/08-Min25.tex)
    - [5.1.9 单位根反演](05-%E6%95%B0%E5%AD%A6/01-%E6%95%B0%E8%AE%BA/09-%E5%8D%95%E4%BD%8D%E6%A0%B9%E5%8F%8D%E6%BC%94.tex)
  - **5.2 组合数学 (Combinatorics)**
    - [5.2.1 组合数 (Binomial Coefficients)](05-%E6%95%B0%E5%AD%A6/02-%E7%BB%84%E5%90%88%E6%95%B0%E5%AD%A6/01-%E7%BB%84%E5%90%88%E6%95%B0.tex)
    - [5.2.2 Lucas 定理 (Lucas's Theorem)](05-%E6%95%B0%E5%AD%A6/02-%E7%BB%84%E5%90%88%E6%95%B0%E5%AD%A6/02-Lucas%20%E5%AE%9A%E7%90%86.tex)
    - [5.2.3 ExLucas (Extended Lucas Theorem)](05-%E6%95%B0%E5%AD%A6/02-%E7%BB%84%E5%90%88%E6%95%B0%E5%AD%A6/03-ExLucas.tex)
    - [5.2.4 min-max 容斥](05-%E6%95%B0%E5%AD%A6/02-%E7%BB%84%E5%90%88%E6%95%B0%E5%AD%A6/04-min-max%20%E5%AE%B9%E6%96%A5.tex)
    - [5.2.5 反演](05-%E6%95%B0%E5%AD%A6/02-%E7%BB%84%E5%90%88%E6%95%B0%E5%AD%A6/05-%E5%8F%8D%E6%BC%94.tex)
  - **5.3 线性代数 (Linear Algebra)**
    - [5.3.1 高斯消元 (Gaussian Elimination)](05-%E6%95%B0%E5%AD%A6/03-%E7%BA%BF%E6%80%A7%E4%BB%A3%E6%95%B0/01-%E9%AB%98%E6%96%AF%E6%B6%88%E5%85%83.tex)
    - [5.3.2 行列式](05-%E6%95%B0%E5%AD%A6/03-%E7%BA%BF%E6%80%A7%E4%BB%A3%E6%95%B0/02-%E8%A1%8C%E5%88%97%E5%BC%8F.tex)
    - [5.3.3 矩阵树定理](05-%E6%95%B0%E5%AD%A6/03-%E7%BA%BF%E6%80%A7%E4%BB%A3%E6%95%B0/03-%E7%9F%A9%E9%98%B5%E6%A0%91%E5%AE%9A%E7%90%86.tex)
    - [5.3.4 BEST 定理 (BEST Theorem)](05-%E6%95%B0%E5%AD%A6/03-%E7%BA%BF%E6%80%A7%E4%BB%A3%E6%95%B0/04-BEST%20%E5%AE%9A%E7%90%86.tex)
    - [5.3.5 LGV 引理 (Weighted LGV Lemma)](05-%E6%95%B0%E5%AD%A6/03-%E7%BA%BF%E6%80%A7%E4%BB%A3%E6%95%B0/05-LGV%20%E5%BC%95%E7%90%86.tex)
  - **5.4 多项式 (Polynomials)**
    - [多项式全家桶（含 vector 精简版）](05-%E6%95%B0%E5%AD%A6/04-%E5%A4%9A%E9%A1%B9%E5%BC%8F/00-%E5%A4%9A%E9%A1%B9%E5%BC%8F%E5%85%A8%E5%AE%B6%E6%A1%B6.tex)
    - [5.4.1 Bostan-Mori](05-%E6%95%B0%E5%AD%A6/04-%E5%A4%9A%E9%A1%B9%E5%BC%8F/01-Bostan-Mori.tex)
  - **5.5 数值方法 (Numerical Methods)**
    - [5.5.1 自适应辛普森 (Adaptive Simpson's Rule)](05-%E6%95%B0%E5%AD%A6/05-%E6%95%B0%E5%80%BC%E6%96%B9%E6%B3%95/01-%E8%87%AA%E9%80%82%E5%BA%94%E8%BE%9B%E6%99%AE%E6%A3%AE.tex)
- **6 Misc**
  - [6.1 C++ 手动上下取整](06-Misc/01-C%2B%2B%20%E6%89%8B%E5%8A%A8%E4%B8%8A%E4%B8%8B%E5%8F%96%E6%95%B4.tex)
  - [6.2 单点修改区间摩尔投票](06-Misc/02-%E5%8D%95%E7%82%B9%E4%BF%AE%E6%94%B9%E5%8C%BA%E9%97%B4%E6%91%A9%E5%B0%94%E6%8A%95%E7%A5%A8.tex)
  - [6.3 双栈模拟 dequeue](06-Misc/03-%E5%8F%8C%E6%A0%88%E6%A8%A1%E6%8B%9F%20dequeue.tex)
  - [6.4 测速](06-Misc/04-%E6%B5%8B%E9%80%9F.tex)
  - [6.5 KKT](06-Misc/05-KKT.tex)
