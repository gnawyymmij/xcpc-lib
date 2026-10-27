"""Extract actual LaTeX listings, compile with C++17, run deterministic differential tests.

Run: python tests/test_templates.py
Requires g++ in PATH. Targets the restored original interfaces. Generated files stay under ignored build/tests/.
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
    if paths[0].parent.name.startswith('05-图匹配') and block==0:
        code=code.replace('// cout<<(-r[0])<<endl;', 'cout<<(-r[0])<<endl;')
    if paths[0].parent.name.startswith('05-图匹配') and block==1:
        code=code.replace('        // cout<<cost<<endl;', '        cout<<cost<<endl;')
    if paths[0].parent.name.startswith('05-数值方法'):
        code=code[:code.rfind('printf(')]
    if paths[0].stem=='01-Bostan-Mori':
        code='void bostan(vector<ll> P,vector<ll> Q,ll m){\n'+code+'\n}'
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
HashTable<ll,ll,128> h;
for(int z=0;z<200;z++){
    h.clear();map<ll,ll> ref;
    for(int i=0;i<100;i++){ll x=rnd(-20,20),v=rnd(-100,100);h[x]=v;ref[x]=v;}
    require(h.size()==int(ref.size()));for(auto [x,v]:ref)require(h.find(x)&&*h.find(x)==v);
    require(!h.find(1000));
}
''')

run('manacher','04-*/03-*.tex',r'''
for(int z=0;z<1000;z++){
    string s;for(int i=rnd(0,45);i--;)s+=char('a'+rnd(0,3));
    copy(s.begin(),s.end(),C+1);C[s.size()+1]=0;run_manacher();int best=0;
    for(int l=0;l<int(s.size());l++)for(int r=l;r<int(s.size());r++){bool ok=true;for(int i=l,j=r;i<j;i++,j--)ok&=s[i]==s[j];if(ok)best=max(best,r-l+1);}
    require(ans==best);
}
''',before='char C[2010],c[4010];ll n,m,md,r,res[4010],ans;',scope='void run_manacher()')

run('aho','04-*/04-*.tex',r'''
for(int z=0;z<200;z++){
    init();vector<string> patterns;vector<int> ends;
    for(int i=0;i<20;i++){
        string s;for(int k=rnd(1,6);k--;)s+=char('a'+rnd(0,2));patterns.push_back(s);
        copy(s.begin(),s.end(),c+1);c[s.size()+1]=0;add(i);int u=1;for(char x:s)u=ch[u][x-'a'];ends.push_back(u);
    }
    gtf();vector<ll> hits(cnt+1);string text;for(int i=0;i<60;i++)text+=char('a'+rnd(0,2));
    int u=1;for(char x:text){u=ch[u][x-'a'];for(int v=u;v!=1;v=fail[v])hits[v]++;}
    for(int i=0;i<20;i++){ll expected=0;for(int k=0;k+patterns[i].size()<=text.size();k++)expected+=text.compare(k,patterns[i].size(),patterns[i])==0;require(hits[ends[i]]==expected);}
}
''',before='ll cnt;char c[2010];')

run('suffix','04-*/05-*.tex',r'''
for(int z=0;z<1000;z++){
    string s;for(int i=rnd(1,70);i--;)s+=char(rnd(1,255));n=s.size();copy(s.begin(),s.end(),c+1);c[n+1]=0;SA();
    vector<int> ref(n);iota(ref.begin(),ref.end(),1);
    sort(ref.begin(),ref.end(),[&](int x,int y){return lexicographical_compare(s.begin()+x-1,s.end(),s.begin()+y-1,s.end(),[](char a,char b){return (unsigned char)a<(unsigned char)b;});});
    for(int i=1;i<=n;i++)require(sa[i]==ref[i-1]&&rk[sa[i]]==i);
    require(he[1]==0);for(int i=2;i<=n;i++){int k=0;while(sa[i]+k<=n&&sa[i-1]+k<=n&&c[sa[i]+k]==c[sa[i-1]+k])k++;require(he[i]==k);}
}
''')

run('pam','04-*/06-*.tex',r'''
for(int z=0;z<100;z++){
    printed.clear();template_main();string text;ll last=0;
    for(int i=1;i<=m;i++){
        text+=char((fake[i]-'a'+last)%26+'a');ll expected=0;
        for(int l=0;l<int(text.size());l++){string s=text.substr(l),r=s;reverse(r.begin(),r.end());expected+=s==r;}
        require(printed[i-1]==expected&&C[i]==text.back());last=expected;
    }
}
''',before=r'''ll n,m,cnt;vector<ll> printed;
int capture_printf(const char* fmt,...){va_list args;va_start(args,fmt);printed.push_back(va_arg(args,ll));va_end(args);return 0;}
#define printf capture_printf
''',input_data='\n'.join('abacaba'*((i*7)%8+1) for i in range(100))+'\n')

run('scc','02-*/01-*/01-*.tex',r'''
for(int z=0;z<700;z++){
    int n=rnd(1,15);init(n);vector<vector<int>> reach(n+1,vector<int>(n+1));
    for(int k=rnd(0,60);k--;){int u=rnd(1,n),v=rnd(1,n);e[u].push_back(v);reach[u][v]=1;}
    for(int i=1;i<=n;i++)reach[i][i]=1;
    for(int k=1;k<=n;k++)for(int i=1;i<=n;i++)for(int j=1;j<=n;j++)reach[i][j]|=reach[i][k]&&reach[k][j];
    for(int i=1;i<=n;i++)if(!dfn[i])dfs(i);
    for(int i=1;i<=n;i++)for(int j=1;j<=n;j++)require((bel[i]==bel[j])==bool(reach[i][j]&&reach[j][i]));
}
''')

run('li_chao','01-*/07-*.tex',r'''
for(int z=0;z<100;z++){
    rt=nd=cnt=0;vector<array<ll,4>> lines;
    for(int k=0;k<100;k++){
        int l=rnd(-30,30),r=rnd(l,30);ll a=rnd(-100,100),b=rnd(-100,100);
        add(l,a*l+b,r,a*r+b);ch(0,2*lim,rt,l+lim,r+lim,cnt);lines.push_back({l,r,a,b});
        for(int x=-35;x<=35;x++){
            double expected=inf;for(auto v:lines)if(v[0]<=x&&x<=v[1])expected=min(expected,double(v[2]*x+v[3]));
            require(fabs(ask(0,2*lim,rt,x+lim)-expected)<1e-6);
        }
    }
}
''')

run('edge_bcc','02-*/01-*/03-*.tex',r'''
for(int z=0;z<350;z++){
    int size=rnd(1,10),count=rnd(0,25);vector<pair<int,int>> input;ostringstream text;text<<size<<' '<<count<<' ';
    for(int i=0;i<count;i++){int u=rnd(1,size),v=rnd(1,size);input.push_back({u,v});text<<u<<' '<<v<<' ';}
    istringstream stream(text.str());cin.rdbuf(stream.rdbuf());template_main();
    auto comps=[&](int skipped){vector<int> label(size+1);int cc=0;for(int u=1;u<=size;u++)if(!label[u]){label[u]=++cc;vector<int> q{u};for(int k=0;k<int(q.size());k++)for(int i=0;i<count;i++)if(i!=skipped){auto [a,b]=input[i];if(a==q[k]&&!label[b])label[b]=cc,q.push_back(b);if(b==q[k]&&!label[a])label[a]=cc,q.push_back(a);}}return cc;};
    int initial=comps(-1);for(int i=0;i<count;i++)require(bool(cut[2*i+2])==(comps(i)>initial));
}
''',before='ll n,m,cnt,hd[500010];struct Edge{ll u,v,nx;};Edge e[4000010];void add(ll u,ll v){e[++cnt]={u,v,hd[u]};hd[u]=cnt;}',block=0)

run('vertex_bcc','02-*/01-*/03-*.tex',r'''
for(int z=0;z<300;z++){
    int size=rnd(1,9),count=rnd(0,25);vector<pair<int,int>> input;ostringstream text;text<<size<<' '<<count<<' ';
    for(int i=0;i<count;i++){int u=rnd(1,size),v=rnd(1,size);input.push_back({u,v});text<<u<<' '<<v<<' ';}
    istringstream stream(text.str());cin.rdbuf(stream.rdbuf());template_main();
    auto connected=[&](int a,int b,int skip){vector<char> vis(size+1);vector<int> q{a};vis[a]=true;for(int k=0;k<int(q.size());k++)for(auto [u,v]:input){if(u==skip||v==skip)continue;if(u==q[k]&&!vis[v])vis[v]=true,q.push_back(v);if(v==q[k]&&!vis[u])vis[u]=true,q.push_back(u);}return bool(vis[b]);};
    for(int a=1;a<=size;a++)for(int b=a+1;b<=size;b++){
        bool expected=connected(a,b,0);for(int k=1;k<=size;k++)if(k!=a&&k!=b)expected&=connected(a,b,k);
        bool together=false;for(int k=1;k<=dcc;k++)together|=find(Dcc[k].begin(),Dcc[k].end(),a)!=Dcc[k].end()&&find(Dcc[k].begin(),Dcc[k].end(),b)!=Dcc[k].end();
        require(together==expected);
    }
    multiset<pair<int,int>> actual,expected;
    for(auto [u,v]:input)if(u!=v)expected.insert(minmax(u,v));
    for(int k=1;k<=dcc;k++)for(auto a:ed[k])actual.insert(minmax(a[0],a[1]));require(actual==expected);
}
''',before='ll n,m;',block=1)

run('negative_cycle','02-*/02-*/*.tex',r'''
for(int z=0;z<700;z++){
    n=rnd(1,10);fill(hd,hd+n+1,0);cnt=0;vector<vector<ll>> dist(n+1,vector<ll>(n+1,1000000));for(int i=1;i<=n;i++)dist[i][i]=0;
    for(int k=rnd(0,30);k--;){int u=rnd(1,n),v=rnd(1,n),w=rnd(-10,10);e[++cnt]={v,w,hd[u]};hd[u]=cnt;dist[u][v]=min(dist[u][v],ll(w));}
    for(int k=1;k<=n;k++)for(int i=1;i<=n;i++)for(int j=1;j<=n;j++)if(dist[i][k]<1000000&&dist[k][j]<1000000)dist[i][j]=min(dist[i][j],dist[i][k]+dist[k][j]);
    bool expected=false;for(int i=1;i<=n;i++)expected|=dist[i][i]<0;require(work()==expected);
}
''',before='ll n,cnt,hd[10010];struct Edge{ll v,w,nx;};Edge e[100010];')

run('farthest','02-*/06-*/02-*.tex',r'''
for(int z=0;z<500;z++){
    int n=rnd(1,60);for(int i=1;i<=n;i++)e[i].clear();
    for(int v=2;v<=n;v++){int u=rnd(1,v-1);e[u].push_back(v);e[v].push_back(u);}
    rt=rnd(1,n);dep[0]=0;getd(rt,0);getf(rt,0,0);
    for(int u=1;u<=n;u++){vector<int> dist(n+1,-1),q{u};dist[u]=0;for(int i=0;i<int(q.size());i++)for(int v:e[q[i]])if(dist[v]<0)dist[v]=dist[q[i]]+1,q.push_back(v);require(max(mx[u]+1,far[u])-1==*max_element(dist.begin()+1,dist.end()));}
}
''',before='ll rt;vector<ll> e[200010];')

run('km','02-*/05-*/*.tex',r'''
for(int z=0;z<350;z++){
    int n=rnd(1,5),m=rnd(n,6);for(int i=1;i<=n;i++)for(int j=1;j<=m;j++)cst[i][j]=rnd(-30,30);
    ll expected=LLONG_MAX;vector<char> used(m+1);function<void(int,ll)> dfs=[&](int i,ll cost){if(i>n){expected=min(expected,cost);return;}for(int j=1;j<=m;j++)if(!used[j])used[j]=true,dfs(i+1,cost+cst[i][j]),used[j]=false;};dfs(1,0);
    ostringstream text;auto previous=cout.rdbuf(text.rdbuf());KM(n,m);cout.rdbuf(previous);require(stoll(text.str())==expected);
}
''',block=0)

run('ssp','02-*/05-*/*.tex',r'''
for(int z=0;z<350;z++){
    int n=rnd(1,5),m=rnd(1,5);for(int i=0;i<=n;i++)e[i].clear();vector<vector<ll>> cost(n+1,vector<ll>(m+1,1000000));
    for(int i=1;i<=n;i++)for(int j=1;j<=m;j++)if(rnd(0,2))cost[i][j]=rnd(-20,20),e[i].push_back({j,cost[i][j]});
    int best=-1;ll expected=0;vector<char> used(m+1);function<void(int,int,ll)> dfs=[&](int i,int count,ll c){if(i>n){if(count>best)best=count,expected=c;else if(count==best)expected=min(expected,c);return;}dfs(i+1,count,c);for(int j=1;j<=m;j++)if(!used[j]&&cost[i][j]<1000000)used[j]=true,dfs(i+1,count+1,c+cost[i][j]),used[j]=false;};dfs(1,0,0);
    ostringstream text;auto previous=cout.rdbuf(text.rdbuf());KM(n,m);cout.rdbuf(previous);istringstream values(text.str());vector<ll> steps;ll v;while(values>>v)steps.push_back(v);require(int(steps.size())==best);require((steps.empty()?0:steps.back())==expected);
}
''',block=1)

run('poly_pointer','05-*/04-*/00-*.tex',r'''
static ll A[4096],B[4096],C[4096],D[4096],E[4096],Q[4096],R[4096];
auto clear_all=[&](){fill(A,A+4096,0);fill(B,B+4096,0);fill(C,C+4096,0);fill(D,D+4096,0);fill(E,E+4096,0);fill(Q,Q+4096,0);fill(R,R+4096,0);};
auto naive=[](const vector<ll>& a,const vector<ll>& b){vector<ll> c(a.size()+b.size()-1);for(int i=0;i<int(a.size());i++)for(int j=0;j<int(b.size());j++)c[i+j]=(c[i+j]+a[i]*b[j])%mod;return c;};
for(int z=0;z<120;z++){
    int n=rnd(0,130),m=rnd(0,130);vector<ll> a(n+1),b(m+1);for(auto &x:a)x=rnd(0,10000);for(auto &x:b)x=rnd(0,10000);
    clear_all();copy(a.begin(),a.end(),A);copy(b.begin(),b.end(),B);poly::Mul(A,B,C,n,m);auto expected=naive(a,b);for(int i=0;i<int(expected.size());i++)require(C[i]==expected[i]);
    a[0]=rnd(1,10000);clear_all();copy(a.begin(),a.end(),A);poly::Inv(A,C,D,n);vector<ll> inv(C,C+n+1);auto identity=naive(a,inv);require(identity[0]==1);for(int i=1;i<=n;i++)require(!identity[i]);
    a[0]=1;clear_all();copy(a.begin(),a.end(),A);poly::Ln(A,C,D,n);copy(C,C+n+1,B);fill(C,C+4096,0);poly::exp(B,C,D,E,n);for(int i=0;i<=n;i++)require(C[i]==a[i]);
    int exponent=rnd(0,5);if(rnd(0,1))a[0]=0;
    clear_all();copy(a.begin(),a.end(),A);poly::pwr(A,C,D,E,Q,n,exponent);vector<ll> power(n+1);power[0]=1;for(int i=0;i<exponent;i++){power=naive(power,a);power.resize(n+1);}for(int i=0;i<=n;i++)require(C[i]==power[i]);
    if(n>=m){
        b.back()=rnd(1,10000);clear_all();copy(a.begin(),a.end(),A);copy(b.begin(),b.end(),B);poly::div(A,B,C,D,E,Q,R,n,m);
        vector<ll> quotient(Q,Q+n-m+1);auto back=naive(quotient,b);back.resize(n+1);for(int i=0;i<=n;i++)require((back[i]+R[i])%mod==a[i]);for(int i=m;i<=n;i++)require(!R[i]);
    }
}
''',block=0)

run('poly_vector','05-*/04-*/00-*.tex',r'''
auto naive=[](const vector<ll>& a,const vector<ll>& b){vector<ll> c(a.size()+b.size()-1);for(int i=0;i<int(a.size());i++)for(int j=0;j<int(b.size());j++)c[i+j]=(c[i+j]+a[i]*b[j])%mod;return c;};
for(int z=0;z<400;z++){
    int n=rnd(1,150),m=rnd(1,150);vector<ll> a(n),b(m);for(auto &x:a)x=rnd(0,10000);for(auto &x:b)x=rnd(0,10000);
    require(Mul(a,b)==naive(a,b));a[0]=rnd(1,10000);auto inverse=Inv(a);auto identity=naive(a,inverse);require(identity[0]==1);for(int i=1;i<n;i++)require(!identity[i]);
}
''',block=1)

run('min25','05-*/01-*/08-*.tex',r'''
ll total=0;
for(int input=1;input<=700;input++){
    ll rest=input,value=1;for(ll p=2;p*p<=rest;p++)if(rest%p==0){ll power=1;while(rest%p==0)rest/=p,power*=p;value=value*(power*(power-1)%mod)%mod;}if(rest>1)value=value*(rest*(rest-1)%mod)%mod;total=(total+value)%mod;
    istringstream stream(to_string(input));ostringstream text;cin.rdbuf(stream.rdbuf());auto previous=cout.rdbuf(text.rdbuf());template_main();cout.rdbuf(previous);require(stoll(text.str())==total);
}
''')

run('steiner','02-*/06-*/03-*.tex',r'''
for(int z=0;z<250;z++){
    int size=rnd(1,6),count=rnd(0,9),term=rnd(1,3);vector<array<int,3>> edges;vector<int> terminals;ostringstream input;input<<size<<' '<<count<<' '<<term<<' ';
    for(int i=0;i<count;i++){int u=rnd(1,size),v=rnd(1,size),w=rnd(0,10);edges.push_back({u,v,w});input<<u<<' '<<v<<' '<<w<<' ';}
    for(int i=0;i<term;i++){int u=rnd(1,size);terminals.push_back(u);input<<u<<' ';}
    ll expected=0x3f3f3f3f3f3f3f3f;for(int mask=0;mask<(1<<count);mask++){
        vector<int> p(size+1);iota(p.begin(),p.end(),0);function<int(int)> find=[&](int u){return p[u]==u?u:p[u]=find(p[u]);};ll cost=0;
        for(int i=0;i<count;i++)if(mask>>i&1){p[find(edges[i][0])]=find(edges[i][1]);cost+=edges[i][2];}
        bool ok=true;for(int u:terminals)ok&=find(u)==find(terminals[0]);if(ok)expected=min(expected,cost);
    }
    istringstream stream(input.str());ostringstream text;cin.rdbuf(stream.rdbuf());auto previous=cout.rdbuf(text.rdbuf());template_main();cout.rdbuf(previous);require(stoll(text.str())==expected);
}
''')

run('euler','02-*/03-*.tex',r'''
for(int z=0;z<500;z++){
    int size=rnd(1,5),count=rnd(0,8);vector<pair<int,int>> edges;ostringstream input;input<<size<<' '<<count<<' ';
    for(int i=0;i<count;i++){int u=rnd(1,size),v=rnd(1,size);edges.push_back({u,v});input<<u<<' '<<v<<' ';}
    bool exists=count==0;vector<char> used(count);function<void(int,int)> search=[&](int u,int length){if(length==count){exists=true;return;}for(int i=0;i<count;i++)if(!used[i]&&edges[i].first==u)used[i]=true,search(edges[i].second,length+1),used[i]=false;};for(int u=1;u<=size;u++)search(u,0);
    istringstream stream(input.str());ostringstream text;cin.rdbuf(stream.rdbuf());auto previous=cout.rdbuf(text.rdbuf());template_main();cout.rdbuf(previous);
    require((text.str().find("No")==string::npos)==exists);
    if(exists){istringstream values(text.str());vector<int> path;int v;while(values>>v)path.push_back(v);require(int(path.size())==count+1);multiset<pair<int,int>> remaining(edges.begin(),edges.end());for(int i=1;i<int(path.size());i++){auto it=remaining.find({path[i-1],path[i]});require(it!=remaining.end());remaining.erase(it);}require(remaining.empty());}
}
''',before='ll n,m;\n#undef pn\n#define pn cout<<"No"<<"\\n"')

run('round_square','02-*/01-*/04-*.tex',r'''
for(int z=0;z<400;z++){
    int size=rnd(1,12),count=rnd(0,30);vector<pair<int,int>> edges;ostringstream input;input<<size<<' '<<count<<' ';
    for(int i=0;i<count;i++){int u=rnd(1,size),v=rnd(1,size);edges.push_back({u,v});input<<u<<' '<<v<<' ';}
    istringstream stream(input.str());cin.rdbuf(stream.rdbuf());template_main();
    vector<int> component(c+1);int label=0;function<void(int,int)> visit=[&](int u,int p){require(!component[u]);component[u]=label;for(int v:E[u])if(v!=p)visit(v,u);};for(int u=1;u<=c;u++)if(!component[u]){label++;visit(u,0);}
    vector<int> original(size+1);iota(original.begin(),original.end(),0);function<int(int)> find=[&](int u){return original[u]==u?u:original[u]=find(original[u]);};for(auto [u,v]:edges)original[find(u)]=find(v);
    for(int u=1;u<=size;u++)for(int v=1;v<=size;v++)require((component[u]==component[v])==(find(u)==find(v)));
}
''')

run('exgcd','05-*/01-*/01-*.tex',r'''
for(int z=0;z<3000;z++){
    ll a=rnd(0,10000),b=rnd(0,10000);if(!a&&!b)continue;c=gcd(a,b)*rnd(-1000,1000);exgcd(a,b);require(a*x+b*y==c);
}
''',before='ll x,y,c;')

run('simpson','05-*/05-*/*.tex',r'''
for(int z=0;z<200;z++){
    a=rnd(1,10);b=rnd(1,10);m=rnd(-10,10);n=rnd(-10,10);double L=rnd(0,10),R=L+rnd(1,10);
    double expected=m/a*(R-L)+(n-m*b/a)/a*log((a*R+b)/(a*L+b));
    require(fabs(asr(L,R,1e-8,simp(L,R))-expected)<1e-6);
}
''',before='#undef f\ndouble m,n,a,b,l,r;')

run('bostan',[('05-*/04-*/00-*.tex',1),('05-*/04-*/01-*.tex',0)],r'''
for(int z=0;z<300;z++){
    vector<ll> P(rnd(0,15)),Q(rnd(1,15));for(auto &x:P)x=rnd(0,10000);for(auto &x:Q)x=rnd(0,10000);Q[0]=rnd(1,10000);int k=rnd(0,100);vector<ll> series(k+1);
    for(int i=0;i<=k;i++){ll v=i<int(P.size())?P[i]:0;for(int j=1;j<=i&&j<int(Q.size());j++)v=(v-series[i-j]*Q[j]%mod+mod)%mod;series[i]=v*qp(Q[0])%mod;}
    bostan(P,Q,k);require(printed==series[k]);
}
''',before=r'''ll printed;
int capture_printf(const char* fmt,...){va_list args;va_start(args,fmt);printed=va_arg(args,ll);va_end(args);return 0;}
#define printf capture_printf
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

run('treap_value','01-*/02-*.tex',r'''
for(int test=0;test<100;test++){
    init();multiset<ll> ref;
    for(int op=0;op<300;op++){
        ll v=rnd(-20,20);
        if(rnd(0,1)){insert(v);ref.insert(v);}else{del(v);auto it=ref.find(v);if(it!=ref.end())ref.erase(it);}
        require(t[rt].sz==ll(ref.size()));int k=1;
        for(ll x:ref)require(findkth(rt,k++)==x);
        require(rk(v)==1+distance(ref.begin(),ref.lower_bound(v)));
    }
    init();insert(1);insert(3);require(pred(3)==1&&succ(1)==3);
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

run('rmq','01-*/03-*.tex',r'''
for(int z=0;z<200;z++){
    int size=rnd(1,200);ostringstream input;input<<size<<" 0 ";vector<ll> a(size+1);
    for(int i=1;i<=size;i++)input<<(a[i]=rnd(-1000,1000))<<' ';
    istringstream stream(input.str());cin.rdbuf(stream.rdbuf());template_main();
    for(int i=0;i<300;i++){int l=rnd(1,size),r=rnd(l,size);require(get(l,r)==*max_element(a.begin()+l,a.begin()+r+1));}
}
{
    int size=100005;ostringstream input;input<<size<<" 0 ";
    for(int i=1;i<=size;i++)input<<i%17<<' ';
    istringstream stream(input.str());cin.rdbuf(stream.rdbuf());template_main();
    require(get(1,size)==16&&get(size,size)==size%17);
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
    for(int i=0;i<500;i++){int u=rnd(1,n),v=rnd(1,n);auto nodes=path(u,v);if(rnd(0,1)){ll x=rnd(-100,100);chad(u,v,(x%mod+mod)%mod);for(int w:nodes)val[w]=(val[w]+x+mod)%mod;}else{ll expect=0;for(int w:nodes)expect=(expect+val[w])%mod;require(chs(u,v)==expect);}}
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

run('division','06-*/01-*.tex',r'''
vector<ll> values{LLONG_MIN,LLONG_MIN+1,-100,-2,-1,0,1,2,100,LLONG_MAX-1,LLONG_MAX};
for(ll x:values)for(ll y:values)if(y&&!(x==LLONG_MIN&&y==-1)){
    __int128_t a=x,b=y,q=a/b,r=a%b;
    require(Floor(x,y)==q-(r&&((r<0)!=(b<0))));require(Ceil(x,y)==q+(r&&((r<0)==(b<0))));
}
''')

run('dynamic_scc','02-*/01-*/02-*.tex',r'''
for(int z=0;z<400;z++){
    int n=rnd(1,10),m=rnd(0,25);for(int i=1;i<=n;i++)fa[i]=i;node.clear();tim=tp=scc=0;
    for(int i=1;i<=n;i++){dfn[i]=low[i]=bel[i]=in[i]=0;e[i].clear();}
    vector<array<int,3>> edges;vector<vector<int>> reach(n+1,vector<int>(n+1));
    for(int i=1;i<=m;i++){U[i]=rnd(1,n);V[i]=rnd(1,n);edges.push_back({U[i],V[i],i});reach[U[i]][V[i]]=1;}
    for(int i=1;i<=n;i++)reach[i][i]=1;
    for(int k=1;k<=n;k++)for(int i=1;i<=n;i++)for(int j=1;j<=n;j++)reach[i][j]|=reach[i][k]&&reach[k][j];
    if(m)work(1,m,edges);
    for(int i=1;i<=n;i++)for(int j=1;j<=n;j++)require((find(i)==find(j))==bool(reach[i][j]&&reach[j][i]));
}
''')

run('mcmf_capacities','02-*/04-*/02-*.tex',r'''
for(int z=0;z<250;z++){
    int size=rnd(2,6),count=rnd(0,8);nodes=size;S=1;T=size;cnt=1;cst=0;fill(hd,hd+nodes+1,0);vector<array<int,4>> input;
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

run('exlucas','05-*/02-*/03-*.tex',r'''
gt();
for(int z=0;z<80;z++){
    int mod=rnd(1,1500),n=rnd(0,30);vector<ll> row(n+1);row[0]=1%mod;
    for(int i=1;i<=n;i++)for(int j=i;j>=1;j--)row[j]=(row[j]+row[j-1])%mod;
    for(int m=0;m<=n+1;m++)require(C(n,m,mod)==(m<=n?row[m]:0));
}
require(C(1000000000000LL,1,1000003)==1000000000000LL%1000003);
require(C(10,3,2000003)==120); // sample modulus size is not an algorithm limit
''',before='ll qp(ll a,ll b,ll p){ll r=1;for(;b;b>>=1,a=a*a%p)if(b&1)r=r*a%p;return r;}')

print(f'{len(passed)} original-interface regression groups passed.')
