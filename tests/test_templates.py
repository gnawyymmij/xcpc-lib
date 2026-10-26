"""Extract actual LaTeX listings, compile with C++17, run deterministic differential tests.

Run: python tests/test_templates.py
Requires g++ in PATH. Generated files stay under ignored build/tests/.
"""
from pathlib import Path
import re
import subprocess
import os

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build' / 'tests'
OUT.mkdir(parents=True, exist_ok=True)
ENV = dict(os.environ)
compiler = __import__('shutil').which('g++')
if not compiler:
    raise SystemExit('g++ is required')
ENV['PATH'] = str(Path(compiler).parent) + os.pathsep + ENV.get('PATH', '')
PRELUDE = r'''
#include <bits/stdc++.h>
using namespace std;
using ll=long long;
#define vi vector<ll>
#define pb push_back
#define f(i,a,b) for(int i=(a);i<=(b);i++)
#define fe(i,e) for(int i=0;i<int((e).size());i++)
#define pn puts("No")
ll rd(){ll x;cin>>x;return x;}
#define wt int tt=d;while(tt--)
mt19937 gen(712367);
int rnd(int l,int r){return uniform_int_distribution<int>(l,r)(gen);}
void require(bool ok){if(!ok)throw runtime_error("regression failed");}
'''

def listing(pattern, block=0):
    paths = list(ROOT.glob(pattern))
    assert len(paths) == 1, (pattern, paths)
    blocks = re.findall(r'\\begin\{lstlisting\}\n(.*?)\\end\{lstlisting\}', paths[0].read_text(encoding='utf-8'), re.S)
    code = blocks[block]
    code = re.sub(r'^#include[^\n]*\n', '', code, flags=re.M)
    if 'int main()' in code:
        start=code.index('{',code.index('int main()'))
        depth=0
        for end in range(start,len(code)):
            depth+=(code[end]=='{')-(code[end]=='}')
            if depth==0:
                code=code[:end]+'\nreturn 0;\n'+code[end:]
                break
        code = code.replace('int main()', 'int template_main()')
    return code

passed = []

def run(name, sources, test, before='', block=0, scope=None, input_data=None):
    if os.environ.get('TEST_ONLY') and name not in os.environ['TEST_ONLY'].split(','):
        return
    if isinstance(sources,str):
        code = listing(sources,block)
    else:
        code = '\n'.join(listing(p,b) for p,b in sources)
    if scope:
        code=scope+'{\n'+code+'\n}\n'
    source = OUT / (name+'.cpp')
    binary = OUT / (name+('.exe' if os.name=='nt' else ''))
    legacy_read = '#define d rd()\n' if re.search(r'=d(?=[;,])|\bwt\b',code) else ''
    prelude=PRELUDE
    if 'inline ll rd()' in code:
        prelude=prelude.replace('ll rd(){ll x;cin>>x;return x;}','')
    source.write_text(prelude+'\n'+legacy_read+before+'\n'+code+'\nint main(){\n'+test+'\n}\n',encoding='utf-8')
    command = [compiler,'-std=c++17','-O2','-Wall','-Wextra','-Wno-misleading-indentation',str(source),'-o',str(binary)]
    result = subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',env=ENV)
    if result.returncode:
        raise RuntimeError(name+' compile failed:\n'+result.stderr)
    result = subprocess.run([str(binary)],input=input_data,capture_output=True,text=True,encoding='utf-8',errors='replace',env=ENV,timeout=90)
    if result.returncode:
        raise RuntimeError(name+' runtime failed:\n'+result.stdout+result.stderr)
    passed.append(name)
    print('PASS',name,flush=True)

run('hash','01-*/01-*.tex',r'''
HashTable<ll,ll,8> h;
for(int test=0;test<200;test++){
    h.clear();require(h.size()==0);for(int i=0;i<8;i++)h[i]=i+test;
    for(int i=0;i<8;i++)require(h.find(i)&&*h.find(i)==i+test);
    require(!h.find(100));bool threw=false;try{h[100]=0;}catch(const overflow_error&){threw=true;}require(threw);
}
''')

run('treap_value','01-*/02-*.tex',r'''
for(int test=0;test<100;test++){
    init();multiset<ll> ref;
    for(int op=0;op<300;op++){
        ll v=rnd(-20,20);if(op==0)v=LLONG_MIN;if(op==1)v=LLONG_MAX;
        if(rnd(0,1)){insert(v);ref.insert(v);}else{del(v);auto it=ref.find(v);if(it!=ref.end())ref.erase(it);}
        require(t[rt].sz==ll(ref.size()));int k=1;
        for(ll x:ref)require(findkth(rt,k++)==x);
        require(rk(v)==1+distance(ref.begin(),ref.lower_bound(v)));
    }
    init();insert(1);bool threw=false;try{pred(1);}catch(const out_of_range&){threw=true;}require(threw&&findkth(rt,1)==1);
}
''')

run('treap_sequence','01-*/02-*.tex',r'''
for(int test=0;test<100;test++){
    init();vector<ll> a(50);iota(a.begin(),a.end(),1);
    for(ll x:a)rt=merge(rt,newnode(x));
    for(int z=0;z<100;z++){
        int l=rnd(0,49),r=rnd(l,49),x,y,w;
        split(rt,r+1,x,w);split(x,l,x,y);t[y].tg^=1;rt=merge(merge(x,y),w);
        reverse(a.begin()+l,a.begin()+r+1);
        vector<ll> b;function<void(int)> visit=[&](int u){if(!u)return;pd(u);visit(ls(u));b.push_back(t[u].val);visit(rs(u));};visit(rt);
        require(a==b);require(t[0].tg==0);
    }
}
''',block=1)

run('li_chao','01-*/07-*.tex',r'''
LiChao tree;
for(int test=0;test<100;test++){
    tree.clear();vector<array<ll,4>> lines;
    for(int z=0;z<100;z++){
        int l=rnd(-30,30),r=rnd(l,30);ll a=rnd(-100,100),b=rnd(-100,100);
        tree.add_segment(l,r,a,b);lines.push_back({l,r,a,b});
        for(int x=-35;x<=35;x++){
            __int128_t best=LiChao::INF;
            for(auto line:lines)if(line[0]<=x&&x<=line[1])best=min(best,(__int128_t)line[2]*x+line[3]);
            require(tree.query(x)==best);
        }
    }
}
tree.clear();tree.add_segment(-1000000000,1000000000,LLONG_MAX,LLONG_MIN);
require(tree.query(1000000000)==(__int128_t)LLONG_MAX*1000000000+LLONG_MIN);
''')

run('lct','01-*/06-*.tex',r'''
for(int test=0;test<40;test++){
    n=25;for(int i=0;i<=n;i++)fa[i]=ch[i][0]=ch[i][1]=val[i]=sum[i]=tg[i]=0;
    vector<set<int>> g(n+1);vector<int> value(n+1);
    auto path=[&](int a,int b){
        vector<int> p(n+1,-1),q{a};p[a]=0;
        for(int i=0;i<int(q.size());i++)for(int v:g[q[i]])if(p[v]<0)p[v]=q[i],q.push_back(v);
        vector<int> result;if(p[b]<0)return result;for(int x=b;x;x=p[x])result.push_back(x);return result;
    };
    for(int z=0;z<1000;z++){
        int a=rnd(1,n),b=rnd(1,n),op=rnd(0,3);
        auto p=path(a,b);
        if(op==0){bool ok=link(a,b);require(ok==p.empty());if(ok)g[a].insert(b),g[b].insert(a);}
        if(op==1){bool expect=g[a].count(b);require(bool(cut(a,b))==expect);if(expect)g[a].erase(b),g[b].erase(a);}
        if(op==2){access(a);splay(a);val[a]=value[a]=rnd(0,1023);upd(a);}
        if(op==3&&!p.empty()){int expect=0;for(int v:p)expect^=value[v];split(a,b);require(sum[b]==expect);}
    }
}
''')

run('manacher','04-*/03-*.tex',r'''
for(int z=0;z<2000;z++){
    string s;for(int i=rnd(0,40);i--;)s+=char(rnd(0,5));int best=0;
    for(int l=0;l<int(s.size());l++)for(int r=l;r<int(s.size());r++){
        bool ok=true;for(int i=l,j=r;i<j;i++,j--)ok&=s[i]==s[j];if(ok)best=max(best,r-l+1);
    }require(manacher(s)==best);
}
''')

run('aho','04-*/04-*.tex',r'''
AhoCorasick ac;
for(int z=0;z<500;z++){
    ac.clear();vector<string> patterns;vector<int> ids;
    for(int i=0;i<20;i++){string p;for(int k=rnd(1,6);k--;)p+=char('a'+rnd(0,2));patterns.push_back(p);ids.push_back(ac.add(p));}
    ac.build();string s;for(int i=0;i<60;i++)s+=char('a'+rnd(0,2));
    auto count=ac.match(s);require(count==ac.match(s));
    for(int i=0;i<20;i++){ll expect=0;for(int k=0;k+patterns[i].size()<=s.size();k++)expect+=s.compare(k,patterns[i].size(),patterns[i])==0;require(count[ids[i]]==expect);}
}
''')

run('suffix','04-*/05-*.tex',r'''
SuffixArray a;
for(int z=0;z<2000;z++){
    string s;for(int i=rnd(0,70);i--;)s+=char(rnd(0,255));a.build(s);
    vector<int> ids(s.size());iota(ids.begin(),ids.end(),0);
    sort(ids.begin(),ids.end(),[&](int x,int y){return lexicographical_compare(s.begin()+x,s.end(),s.begin()+y,s.end(),[](char a,char b){return (unsigned char)a<(unsigned char)b;});});
    require(a.sa==ids);for(int i=1;i<int(ids.size());i++){int h=0;while(ids[i]+h<int(s.size())&&ids[i-1]+h<int(s.size())&&s[ids[i]+h]==s[ids[i-1]+h])h++;require(a.lcp[i]==h);}
}
''')

run('pam','04-*/06-*.tex',r'''
PalindromicTree p;
for(int z=0;z<500;z++){
    p.clear();string s;set<string> all;map<string,ll> freq;
    for(int i=0;i<60;i++){
        s+=char('a'+rnd(0,2));int expected=0;
        for(int l=0;l<=i;l++){string t=s.substr(l);string r=t;reverse(r.begin(),r.end());if(t==r)expected++,all.insert(t),freq[t]++;}
        require(p.add(s.back())==expected);require(p.t.size()==all.size()+2);
    }
    auto count=p.occurrences();require(count==p.occurrences());
    ll sum=accumulate(count.begin()+2,count.end(),0LL),expect=0;for(auto [s,v]:freq)expect+=v;require(sum==expect);
}
''')

run('bcc',[('02-*/01-*/03-*.tex',0),('02-*/01-*/04-*.tex',0)],r'''
Biconnected b;
for(int z=0;z<600;z++){
    int n=rnd(1,12),m=rnd(0,30);b.init(n);
    for(int i=0;i<m;i++)b.add(rnd(1,n),rnd(1,n));b.run();auto old=b.bridge;b.run();require(old==b.bridge);
    auto comps=[&](int skipped){vector<int> c(n+1);int cc=0;for(int u=1;u<=n;u++)if(!c[u]){vector<int> q{u};c[u]=++cc;for(int k=0;k<int(q.size());k++)for(int i=0;i<m;i++)if(i!=skipped){auto [a,v]=b.edges[i];if(a==q[k]&&!c[v])c[v]=cc,q.push_back(v);if(v==q[k]&&!c[a])c[a]=cc,q.push_back(a);}}return cc;};
    int baseline=comps(-1);for(int i=0;i<m;i++)require(bool(b.bridge[i])==(comps(i)>baseline));
    vector<int> seen(m);for(auto ids:b.block_edges)for(int i:ids)seen[i]++;
    for(int i=0;i<m;i++)require(seen[i]==(b.edges[i].first!=b.edges[i].second));
    auto tree=block_cut_forest(b);vector<int> vis(tree.size());function<void(int,int)> dfs=[&](int u,int p){require(!vis[u]);vis[u]=1;for(int v:tree[u])if(v!=p)dfs(v,u);};
    for(int u=1;u<int(tree.size());u++)if(!vis[u])dfs(u,0);
}
''')

run('negative_cycle','02-*/02-*/*.tex',r'''
for(int z=0;z<1000;z++){
    int n=rnd(1,10);vector<vector<pair<int,ll>>> g(n+1);vector<vector<ll>> a(n+1,vector<ll>(n+1,1000000));
    for(int i=1;i<=n;i++)a[i][i]=0;
    for(int k=rnd(0,30);k--;){int u=rnd(1,n),v=rnd(1,n),w=rnd(-10,10);g[u].push_back({v,w});a[u][v]=min(a[u][v],ll(w));}
    for(int k=1;k<=n;k++)for(int i=1;i<=n;i++)for(int j=1;j<=n;j++)if(a[i][k]<1000000&&a[k][j]<1000000)a[i][j]=min(a[i][j],a[i][k]+a[k][j]);
    bool expected=false;for(int i=1;i<=n;i++)expected|=a[i][i]<0;
    require(negative_cycle(g)==expected);
}
''')

run('euler','02-*/03-*.tex',r'''
for(int z=0;z<600;z++){
    int n=rnd(1,5),m=rnd(0,8);vector<pair<int,int>> e;
    for(int i=0;i<m;i++)e.push_back({rnd(1,n),rnd(1,n)});
    bool exists=m==0;vector<char> used(m);
    function<void(int,int)> dfs=[&](int u,int count){if(count==m){exists=true;return;}for(int i=0;i<m;i++)if(!used[i]&&e[i].first==u){used[i]=true;dfs(e[i].second,count+1);used[i]=false;}};
    for(int i=1;i<=n;i++)dfs(i,0);auto p=euler_directed(n,e);require(!p.empty()==exists);
    if(exists){multiset<pair<int,int>> ref(e.begin(),e.end());for(int i=1;i<int(p.size());i++){auto it=ref.find({p[i-1],p[i]});require(it!=ref.end());ref.erase(it);}require(ref.empty());}
}
''')

run('dinic','02-*/04-*/01-*.tex',r'''
for(int z=0;z<500;z++){
    nodes=rnd(2,8);S=1;T=nodes;cnt=1;fill(hd,hd+nodes+1,0);
    vector<array<ll,3>> input;
    for(int k=rnd(0,30);k--;){int u=rnd(1,nodes),v=rnd(1,nodes);ll w=rnd(0,100);ad(u,v,w);input.push_back({u,v,w});}
    ll best=LLONG_MAX;for(int mask=0;mask<(1<<nodes);mask++)if((mask&1)&&!(mask>>(T-1)&1)){
        ll total=0;for(auto a:input)if((mask>>(a[0]-1)&1)&&!(mask>>(a[1]-1)&1))total+=a[2];best=min(best,total);
    }
    require(dinic()==best);require(dinic()==0);
}
''')

run('km','02-*/05-*/*.tex',r'''
for(int z=0;z<400;z++){
    int n=rnd(1,5),m=rnd(n,6);for(int i=1;i<=n;i++)for(int j=1;j<=m;j++)cst[i][j]=rnd(-30,30);
    ll best=LLONG_MAX;vector<char> used(m+1);function<void(int,ll)> dfs=[&](int i,ll c){if(i>n){best=min(best,c);return;}for(int j=1;j<=m;j++)if(!used[j])used[j]=1,dfs(i+1,c+cst[i][j]),used[j]=0;};dfs(1,0);
    auto result=KM(n,m);require(result.first==best);
}
''')

run('mcmf',[('02-*/04-*/02-*.tex',0),('02-*/05-*/*.tex',1)],r'''
for(int z=0;z<400;z++){
    int n=rnd(1,5),m=rnd(1,5);vector<tuple<int,int,ll>> input;vector<vector<ll>> c(n+1,vector<ll>(m+1,1000000));
    for(int i=1;i<=n;i++)for(int j=1;j<=m;j++)if(rnd(0,2))c[i][j]=rnd(-20,20),input.push_back({i,j,c[i][j]});
    int best_count=-1;ll best=0;vector<char> used(m+1);
    function<void(int,int,ll)> dfs=[&](int i,int count,ll cost){if(i>n){if(count>best_count)best_count=count,best=cost;else if(count==best_count)best=min(best,cost);return;}dfs(i+1,count,cost);for(int j=1;j<=m;j++)if(!used[j]&&c[i][j]<1000000)used[j]=1,dfs(i+1,count+1,cost+c[i][j]),used[j]=0;};dfs(1,0,0);
    auto result=sparse_matching(n,m,input);require(result[0]==best_count&&result[1]==best);
}
''')

run('farthest','02-*/06-*/02-*.tex',r'''
for(int z=0;z<400;z++){
    int n=rnd(1,60);for(int i=1;i<=n;i++)e[i].clear();
    for(int v=2;v<=n;v++){int u=rnd(1,v-1);e[u].push_back(v);e[v].push_back(u);}
    int root=rnd(1,n);dfs_down(root,0);up[root]=0;dfs_up(root,0);
    for(int u=1;u<=n;u++){vector<int> dist(n+1,-1),q{u};dist[u]=0;for(int i=0;i<int(q.size());i++)for(int v:e[q[i]])if(dist[v]<0)dist[v]=dist[q[i]]+1,q.push_back(v);require(max(down[u],up[u])==*max_element(dist.begin()+1,dist.end()));}
}
''')

run('steiner','02-*/06-*/03-*.tex',r'''
for(int z=0;z<300;z++){
    int n=rnd(1,6),m=rnd(0,9);vector<vector<pair<int,ll>>> g(n+1);vector<array<int,3>> edges;
    for(int i=0;i<m;i++){int u=rnd(1,n),v=rnd(1,n),w=rnd(0,10);edges.push_back({u,v,w});g[u].push_back({v,w});g[v].push_back({u,w});}
    vector<int> terminal;for(int i=rnd(0,3);i--;)terminal.push_back(rnd(1,n));
    ll best=LLONG_MAX/4;if(terminal.empty())best=0;
    for(int mask=0;mask<(1<<m);mask++){
        vector<int> p(n+1);iota(p.begin(),p.end(),0);function<int(int)> find=[&](int x){return p[x]==x?x:p[x]=find(p[x]);};ll c=0;
        for(int i=0;i<m;i++)if(mask>>i&1){p[find(edges[i][0])]=find(edges[i][1]);c+=edges[i][2];}
        bool ok=true;for(int u:terminal)ok&=find(u)==find(terminal[0]);if(ok)best=min(best,c);
    }
    require(steiner_tree(g,terminal)==best);
}
''')

run('scc_2sat',[('02-*/01-*/01-*.tex',0),('02-*/07-*.tex',0)],r'''
for(int z=0;z<1000;z++){
    int n=rnd(1,7);init(2*n);vector<pair<int,int>> clauses;
    for(int k=rnd(0,25);k--;){int a=rnd(1,2*n),b=rnd(1,2*n);clauses.push_back({a,b});add_clause(a,b,n);}
    auto literal=[&](int a,int mask){return a<=n?!(mask>>(a-1)&1):bool(mask>>(a-n-1)&1);};
    bool exists=false;for(int mask=0;mask<(1<<n);mask++){bool ok=true;for(auto [a,b]:clauses)ok&=literal(a,mask)||literal(b,mask);exists|=ok;}
    auto result=solve_2sat(n);require(bool(result)==exists);
    if(result){int mask=0;for(int i=1;i<=n;i++)mask|=(*result)[i]<<(i-1);for(auto [a,b]:clauses)require(literal(a,mask)||literal(b,mask));}
}
''')

run('dynamic_scc','02-*/01-*/02-*.tex',r'''
for(int z=0;z<400;z++){
    int n=rnd(1,10),m=rnd(0,25);init_dsu(n);node.clear();tim=tp=scc=0;
    for(int i=1;i<=n;i++){dfn[i]=low[i]=bel[i]=in[i]=0;e[i].clear();}
    vector<array<int,3>> edges;vector<vector<int>> reach(n+1,vector<int>(n+1));
    for(int i=1;i<=m;i++){U[i]=rnd(1,n);V[i]=rnd(1,n);edges.push_back({U[i],V[i],i});reach[U[i]][V[i]]=1;}
    for(int i=1;i<=n;i++)reach[i][i]=1;
    for(int k=1;k<=n;k++)for(int i=1;i<=n;i++)for(int j=1;j<=n;j++)reach[i][j]|=reach[i][k]&&reach[k][j];
    if(m)work(1,m,edges);
    for(int i=1;i<=n;i++)for(int j=1;j<=n;j++)require((find(i)==find(j))==bool(reach[i][j]&&reach[j][i]));
}
''')

run('exgcd','05-*/01-*/01-*.tex',r'''
for(int z=0;z<3000;z++){
    ll a=rnd(0,10000),b=rnd(0,10000),c=rnd(-100000,100000);__int128_t x,y;
    bool ok=diophantine(a,b,c,x,y);require(ok==(a||b?c%gcd(a,b)==0:c==0));if(ok)require(a*x+b*y==c);
}
''')

run('floor_sum','05-*/01-*/02-*.tex',r'''
for(int z=0;z<2000;z++){
    ll n=rnd(1,100),m=rnd(1,100),a=rnd(0,100),b=rnd(0,100);node U{0,1,0},R{0,0,1};
    auto result=opow(U,b/m)+work(a,b%m,n-1,m,U,R);ll expected=0;
    for(int i=0;i<n;i++)expected+=(a*i+b)/m;require(result.s+b/m==expected);
}
''',before='ll n,m;')

run('crt','05-*/01-*/03-*.tex',r'''
for(int z=0;z<2000;z++){
    ll B=rnd(1,50),b=rnd(1,50),A=rnd(-100,100),a=rnd(-100,100),oldA=A,oldB=B;
    ll period=lcm(B,b),expected=-1;
    for(ll x=0;x<period;x++)if((x-A)%B==0&&(x-a)%b==0){expected=x;break;}
    bool ok=merge(A,B,a,b);require(ok==(expected!=-1));if(ok)require(A==expected&&B==period);else require(A==oldA&&B==oldB);
}
ll A=0,B=LLONG_MAX;bool threw=false;try{merge(A,B,0,2);}catch(const overflow_error&){threw=true;}require(threw);
''')

run('pollard','05-*/01-*/05-*.tex',r'''
for(ll x=1;x<=30000;x++){
    bool prime=x>=2;for(ll p=2;p*p<=x;p++)if(x%p==0){prime=false;break;}
    require(miller(x)==prime);
}
for(int z=0;z<1000;z++){
    ll x=rnd(2,10000000),copy=x,largest=0;
    for(ll p=2;p*p<=copy;p++)while(copy%p==0)largest=p,copy/=p;if(copy>1)largest=copy;
    mxp=0;work(x);require(mxp==largest);
}
require(miller(2305843009213693951LL));
''')

run('du_sieve','05-*/01-*/07-*.tex',r'''
gt();gt();vector<ll> mus(2100011),phis(2100011);vector<int> primes;vector<int> least(2100011);mus[1]=phis[1]=1;
for(int i=2;i<=2100010;i++){
    if(!least[i])least[i]=i,primes.push_back(i),mus[i]=-1,phis[i]=i-1;
    for(int p:primes){if(ll(i)*p>2100010)break;least[i*p]=p;if(i%p==0){phis[i*p]=phis[i]*p;break;}mus[i*p]=-mus[i];phis[i*p]=phis[i]*(p-1);}
}
for(int i=1;i<=2100010;i++)mus[i]+=mus[i-1],phis[i]+=phis[i-1];
for(int i=0;i<100;i++){int x=rnd(0,2100010);require(Mu(x)==mus[x]&&Ph(x)==phis[x]);}
require(Mu(2000001)==mus[2000001]);require(Mu(2000001)==mus[2000001]);
''',before='ll cnt;')

run('min25','05-*/01-*/08-*.tex',r'''
Min25 sieve;ll total=0;
for(int n=1;n<=3000;n++){
    ll value=1,rest=n;for(ll p=2;p*p<=rest;p++)if(rest%p==0){ll pk=1;while(rest%p==0)rest/=p,pk*=p;value=value*(pk*(pk-1)%Min25::mod)%Min25::mod;}
    if(rest>1)value=value*(rest*(rest-1)%Min25::mod)%Min25::mod;total=(total+value)%Min25::mod;
    require(sieve.sum(n)==total);
}
require(sieve.sum(1)==1&&sieve.sum(0)==0);
''')

run('exlucas','05-*/02-*/03-*.tex',r'''
for(int z=0;z<500;z++){
    int mod=rnd(1,1500),n=rnd(0,70);vector<ll> row(n+1);row[0]=1%mod;
    for(int i=1;i<=n;i++)for(int j=i;j>=1;j--)row[j]=(row[j]+row[j-1])%mod;
    for(int m=0;m<=n+1;m++)require(exlucas(n,m,mod)==(m<=n?row[m]:0));
}
require(exlucas(1000000000000LL,1,1000003)==1000000000000LL%1000003);
''')

run('poly',[('05-*/04-*/00-*.tex',0),('05-*/04-*/01-*.tex',0)],r'''
using namespace poly;
auto naive=[](const Poly& a,const Poly& b){if(a.empty()||b.empty())return Poly{};Poly c(a.size()+b.size()-1);for(int i=0;i<int(a.size());i++)for(int j=0;j<int(b.size());j++)c[i+j]=(c[i+j]+a[i]*b[j])%mod;return c;};
for(int z=0;z<400;z++){
    int n=rnd(1,130),m=rnd(1,130);Poly a(n),b(m);for(ll &x:a)x=rnd(0,10000);for(ll &x:b)x=rnd(0,10000);
    require(Mul(a,b)==naive(a,b));a[0]=rnd(1,10000);
    Poly inv=Inv(a,n),prod=naive(a,inv);prod.resize(n);require(prod[0]==1);for(int i=1;i<n;i++)require(!prod[i]);
    a[0]=1;require(Exp(Ln(a,n),n)==a);
    a[0]=0;require(Ln(Exp(a,n),n)==a);
    int exponent=rnd(0,7);if(rnd(0,1))a[0]=rnd(1,10000);if(n>1&&rnd(0,1))a[1]=0;
    Poly expect(n);expect[0]=1;for(int i=0;i<exponent;i++){expect=naive(expect,a);expect.resize(n);}require(Pow(a,exponent,n)==expect);
    b[0]=rnd(1,10000);auto [q,r]=Div(a,b);Poly back=naive(q,b);back.resize(max(back.size(),r.size()));for(int i=0;i<int(r.size());i++)back[i]=(back[i]+r[i])%mod;trim(back);Poly original=a;trim(original);require(back==original&&r.size()<b.size());
    int k=rnd(0,180);Poly series(k+1);for(int i=0;i<=k;i++){ll v=i<int(a.size())?a[i]:0;for(int j=1;j<=i&&j<int(b.size());j++)v=(v-series[i-j]*b[j]%mod+mod)%mod;series[i]=v*qp(b[0])%mod;}
    require(bostan_mori(a,b,k)==series[k]);
}
require(bostan_mori({},Poly{1},100)==0);require(bostan_mori(Poly{1},Poly{1},100)==0);
require(Pow(Poly{0},0,3)==Poly({1,0,0}));require(Pow(Poly{0},4,3)==Poly({0,0,0}));
''')

run('simpson','05-*/05-*/*.tex',r'''
for(int z=0;z<200;z++){
    double a=rnd(-30,30),b=rnd(-30,30);auto f=[](double x){return x*x*x*x;};
    double expected=(pow(b,5)-pow(a,5))/5;require(fabs(integrate(f,a,b,1e-7)-expected)<1e-5);
}
require(fabs(integrate([](double x){return sin(x);},0,acos(-1))-2)<1e-8);
''')

run('division','06-*/01-*.tex',r'''
vector<ll> values{LLONG_MIN,LLONG_MIN+1,-100,-2,-1,0,1,2,100,LLONG_MAX-1,LLONG_MAX};
for(ll x:values)for(ll y:values)if(y&&!(x==LLONG_MIN&&y==-1)){
    __int128_t a=x,b=y,q=a/b,r=a%b;
    require(Floor(x,y)==q-(r&&((r<0)!=(b<0))));require(Ceil(x,y)==q+(r&&((r<0)==(b<0))));
}
''')

run('rmq','01-*/03-*.tex',r'''
for(int z=0;z<200;z++){
    int size=rnd(1,200);ostringstream input;input<<size<<" 0 ";vector<ll> a(size+1);
    for(int i=1;i<=size;i++)input<<(a[i]=rnd(-1000,1000))<<' ';
    istringstream stream(input.str());cin.rdbuf(stream.rdbuf());template_main();
    for(int i=0;i<300;i++){int l=rnd(1,size),r=rnd(l,size);require(get(l,r)==*max_element(a.begin()+l,a.begin()+r+1));}
}
''',before='ll n,m;')

run('cartesian','01-*/04-*.tex',r'''
for(int z=0;z<200;z++){
    int size=rnd(1,200);ostringstream input;input<<size<<' ';
    for(int i=1;i<=size;i++)input<<rnd(-30,30)<<' ';
    istringstream stream(input.str());cin.rdbuf(stream.rdbuf());template_main();
    vector<int> order;function<void(int)> visit=[&](int u){if(!u)return;if(l[u])require(a[u]<=a[l[u]]);if(r[u])require(a[u]<=a[r[u]]);visit(l[u]);order.push_back(u);visit(r[u]);};visit(st[1]);
    require(int(order.size())==size);for(int i=0;i<size;i++)require(order[i]==i+1);
}
''',before='ll n;')

run('hld','01-*/05-*.tex',r'''
for(int z=0;z<100;z++){
    n=rnd(1,50);tim=cnt=0;sz[0]=de[0]=0;fill(hd,hd+n+1,0);
    vector<vector<int>> g(n+1);vector<ll> val(n+1);
    auto edge=[&](int u,int v){e[++cnt]={v,(int)hd[u]};hd[u]=cnt;};
    for(int v=2;v<=n;v++){int u=rnd(1,v-1);edge(u,v);edge(v,u);g[u].push_back(v);g[v].push_back(u);}
    for(int i=1;i<=n;i++)val[i]=a[i]=rnd(0,100);int root=rnd(1,n);dfs1(root,0);dfs2(root,root);build(1,n,1);
    auto path=[&](int u,int v){vector<int> p(n+1,-1),q{u};p[u]=0;for(int i=0;i<int(q.size());i++)for(int x:g[q[i]])if(p[x]<0)p[x]=q[i],q.push_back(x);vector<int> out;for(int x=v;x;x=p[x])out.push_back(x);return out;};
    for(int i=0;i<500;i++){int u=rnd(1,n),v=rnd(1,n);auto nodes=path(u,v);if(rnd(0,1)){ll x=rnd(-100,100);chad(u,v,x);for(int w:nodes)val[w]=(val[w]+x+mod)%mod;}else{ll expect=0;for(int w:nodes)expect=(expect+val[w])%mod;require(chs(u,v)==expect);}}
}
''',before='ll n,tim,cnt;const ll mod=1000000007;struct Edge{int v,nx;};Edge e[200010];ll hd[100010];')

run('wqs','03-*/01-*.tex',r'''
for(int z=0;z<200;z++){
    n=rnd(1,25);prefix[0]=0;for(int i=1;i<=n;i++)prefix[i]=prefix[i-1]+rnd(0,10);
    vector<vector<ll>> ref(n+1,vector<ll>(n+1,INF));ref[0][0]=0;
    for(int i=1;i<=n;i++)for(int k=1;k<=i;k++)for(int j=k-1;j<i;j++)ref[i][k]=min(ref[i][k],ref[j][k-1]+cost(j+1,i));
    for(int k=1;k<=n;k++)require(wqs(k,-1000000,1000000)==ref[n][k]);
}
''',before='const int N=100;const ll INF=LLONG_MAX/4;int n;ll prefix[N];ll cost(int l,int r){ll x=prefix[r]-prefix[l-1];return x*x;}')

run('decision_queue','03-*/02-*.tex',r'''
for(int z=0;z<1500;z++){
    n=rnd(1,70);prefix[0]=0;for(int i=1;i<=n;i++)prefix[i]=prefix[i-1]+rnd(0,10);ll extra=rnd(-1000,1000);
    solve_dp(extra);vector<pair<ll,int>> ref(n+1);for(int i=1;i<=n;i++){ref[i]={LLONG_MAX/4,0};for(int j=0;j<i;j++)ref[i]=min(ref[i],pair<ll,int>{ref[j].first+cost(j+1,i)+extra,ref[j].second+1});require(ref[i]==make_pair(dp[i],cnt[i]));}
}
''',before='const int N=100;int n;ll prefix[N];ll cost(int l,int r){ll x=prefix[r]-prefix[l-1];return x*x;}')

run('centroid','02-*/06-*/01-*.tex',r'''
for(int z=0;z<500;z++){
    int n=rnd(1,50);fill(hd,hd+n+1,0);fill(fl,fl+n+1,false);int cnt=0;
    vector<vector<int>> graph(n+1);for(int v=2;v<=n;v++){int u=rnd(1,v-1);e[++cnt]={v,0,(int)hd[u]};hd[u]=cnt;e[++cnt]={u,0,(int)hd[v]};hd[v]=cnt;graph[u].push_back(v);graph[v].push_back(u);}
    for(int i=1;i<=n;i++)if(rnd(0,4)==0)fl[i]=true;
    int root=rnd(1,n);fl[root]=false;getg(root);require(g&&!fl[g]);
    vector<char> seen(n+1);vector<int> q{root};seen[root]=true;for(int i=0;i<int(q.size());i++)for(int v:graph[q[i]])if(!fl[v]&&!seen[v])seen[v]=true,q.push_back(v);
    int total=q.size(),worst=0;seen.assign(n+1,false);seen[g]=true;
    for(int v:graph[g])if(!fl[v]){vector<int> st{v};seen[v]=true;for(int i=0;i<int(st.size());i++)for(int w:graph[st[i]])if(!fl[w]&&!seen[w])seen[w]=true,st.push_back(w);worst=max(worst,int(st.size()));}
    require(worst*2<=total);
}
''',before='struct Edge{ll v,w,nx;};Edge e[200010];ll hd[100010];')

run('binom','05-*/02-*/01-*.tex',r'''
binom::pre();binom::pre();vector<ll> row(200);row[0]=1;
for(int n=0;n<190;n++){if(n)for(int k=n;k>=1;k--)row[k]=(row[k]+row[k-1])%binom::mod;for(int k=0;k<=n+1;k++)require(binom::C(n,k)==(k<=n?row[k]:0));}
''')

run('det','05-*/03-*/02-*.tex',r'''
for(int z=0;z<500;z++){
    int n=rnd(0,6);vector<vector<ll>> original(n,vector<ll>(n));for(int i=0;i<n;i++)for(int j=0;j<n;j++)matrix[i+1][j+1]=original[i][j]=rnd(-10,10);
    vector<int> p(n);iota(p.begin(),p.end(),0);ll expect=0;
    do{int parity=0;ll product=1;for(int i=0;i<n;i++){product=product*original[i][p[i]]%mod;for(int j=0;j<i;j++)parity^=p[j]>p[i];}expect=(expect+(parity?-product:product))%mod;}while(next_permutation(p.begin(),p.end()));
    require(det(n,matrix)==(expect+mod)%mod);
}
''',before='const ll mod=1000000007;ll matrix[1010][1010];')

run('gauss','05-*/03-*/01-*.tex',r'''
for(int z=0;z<100;z++){
    int size=rnd(1,12);vector<double> solution(size);for(auto &x:solution)x=rnd(-100,100)/10.0;ostringstream input;input<<setprecision(17)<<size<<' ';
    for(int i=0;i<size;i++){vector<double> row(size);for(auto &x:row)x=rnd(-10,10)/10.0;row[i]+=100;double rhs=0;for(int j=0;j<size;j++)rhs+=row[j]*solution[j],input<<row[j]<<' ';input<<rhs<<' ';}
    istringstream stream(input.str());cin.rdbuf(stream.rdbuf());template_main();
    for(int i=0;i<size;i++)require(fabs(b[i+1]-solution[i])<1e-8);
}
''',before='ll n;')

run('string_hash','04-*/01-*.tex',r'''
for(int z=0;z<50;z++){
    template_main();for(int k=0;k<100;k++){
        int l=rnd(1,n),r=rnd(l,n);ll expect=0;
        for(int i=l;i<=r;i++)expect=(expect*bs+c[i]-'a'+1)%mod;
        require(get(l,r)==expect);
    }
}
''',input_data='\n'.join(('abacaba'*((i*7)%40+1)) for i in range(50))+'\n')

run('kmp','04-*/02-*.tex',r'''
for(int z=0;z<500;z++){
    string a,b;for(int k=rnd(1,80);k--;)a+=char('a'+rnd(0,2));for(int k=rnd(1,10);k--;)b+=char('a'+rnd(0,2));
    istringstream input(a+" "+b);ostringstream output;auto oldin=cin.rdbuf(input.rdbuf());auto oldout=cout.rdbuf(output.rdbuf());template_main();cin.rdbuf(oldin);cout.rdbuf(oldout);
    ostringstream expect;for(int i=0;i+b.size()<=a.size();i++)if(a.compare(i,b.size(),b)==0)expect<<i+1<<'\n';require(output.str()==expect.str());
}
''',before='ll n,m;')

run('dirichlet','05-*/01-*/06-*.tex',r'''
for(int z=0;z<500;z++){
    n=rnd(1,500);cnt=0;for(int x=2;x<=n;x++){bool prime=true;for(int p=2;p*p<=x;p++)if(x%p==0)prime=false;if(prime)pr[++cnt]=x;}
    vector<ll> original(n+1);for(int i=1;i<=n;i++)a[i]=original[i]=rnd(-100,100);transform();
    for(int x=1;x<=n;x++){ll expected=0;for(int k=1;k<=x;k++)if(x%k==0)expected+=original[k];require(a[x]==expected);}
}
''',before='ll i,j,n,cnt,pr[1010],a[1010];',scope='void transform()')

run('matrix_tree',[('05-*/03-*/02-*.tex',0),('05-*/03-*/03-*.tex',0)],r'''
for(int z=0;z<200;z++){
    int size=rnd(1,5),count=rnd(0,8),type=rnd(0,1);vector<array<int,3>> edges;
    ostringstream input;input<<size<<' '<<count<<' '<<type<<' ';
    for(int i=0;i<count;i++){int u=rnd(1,size),v=rnd(1,size),w=rnd(0,5);edges.push_back({u,v,w});input<<u<<' '<<v<<' '<<w<<' ';}
    istringstream stream(input.str());cin.rdbuf(stream.rdbuf());solve();
    // Independently enumerate all n-1 edge sets with correct root orientation.
    ll expected=0;for(int mask=0;mask<(1<<count);mask++)if(__builtin_popcount(unsigned(mask))==size-1){
        vector<vector<int>> g(size+1);vector<int> indeg(size+1);ll product=1;
        for(int i=0;i<count;i++)if(mask>>i&1){auto edge=edges[i];g[edge[0]].push_back(edge[1]);indeg[edge[1]]++;if(!type)g[edge[1]].push_back(edge[0]);product=product*edge[2]%mod;}
        bool ok=true;if(type){ok=indeg[1]==0;for(int u=2;u<=size;u++)ok&=indeg[u]==1;}
        vector<char> vis(size+1);vector<int> q{1};vis[1]=true;for(int i=0;i<int(q.size());i++)for(int v:g[q[i]])if(!vis[v])vis[v]=true,q.push_back(v);
        if(ok&&int(q.size())==size)expected=(expected+product)%mod;
    }
    require(printed==expected);
}
''',before=r'''const ll mod=1000000007;ll n,m,a[1010][1010],printed;
int capture_printf(const char* format,...){va_list args;va_start(args,format);printed=va_arg(args,ll);va_end(args);return 0;}
#define printf capture_printf
''')

run('moore','06-*/02-*.tex',r'''
for(int z=0;z<500;z++){
    int n=rnd(1,80);vector<int> a(n);for(int &x:a)x=rnd(-1,5);
    function<Vote(int,int)> query=[&](int l,int r)->Vote{if(l==r)return {a[l],1};int mid=(l+r)/2;return merge_vote(query(l,mid),query(mid+1,r));};
    for(int k=0;k<100;k++){int l=rnd(0,n-1),r=rnd(l,n-1);map<int,int> freq;for(int i=l;i<=r;i++)freq[a[i]]++;auto vote=query(l,r);for(auto [value,count]:freq)if(count*2>r-l+1)require(vote.count&&vote.candidate==value);}
}
''')

run('mcmf_capacities','02-*/04-*/02-*.tex',r'''
for(int z=0;z<250;z++){
    int size=rnd(2,6),count=rnd(0,8);init_mcmf(size,1,size);vector<array<int,4>> input;
    bool dag=rnd(0,1);
    for(int i=0;i<count;i++){
        int u=rnd(1,size),v=rnd(1,size);if(dag){u=rnd(1,size-1);v=rnd(u+1,size);}
        int capacity=rnd(0,2),cost=dag?rnd(-8,8):rnd(0,8);input.push_back({u,v,capacity,cost});ad(u,v,capacity,cost);
    }
    ll best_flow=-1,best_cost=0;vector<int> balance(size+1);
    function<void(int,ll)> enumerate=[&](int i,ll cost){
        if(i==count){for(int u=2;u<size;u++)if(balance[u])return;ll flow=-balance[1];if(flow<0||balance[size]!=flow)return;if(flow>best_flow)best_flow=flow,best_cost=cost;else if(flow==best_flow)best_cost=min(best_cost,cost);return;}
        auto edge=input[i];for(int amount=0;amount<=edge[2];amount++){
            balance[edge[0]]-=amount;balance[edge[1]]+=amount;enumerate(i+1,cost+ll(amount)*edge[3]);balance[edge[0]]+=amount;balance[edge[1]]-=amount;
        }
    };enumerate(0,0);spfa(S);auto result=mcmf();require(result[0]==best_flow&&result[1]==best_cost);
}
''')

print(f'{len(passed)} extracted-template regression groups passed.')
