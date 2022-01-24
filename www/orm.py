import sqlite3
import asyncio,logging,aiomysql

def log(sql, args=()):
    logging.info('SQL: %s' % sql)

async def create_pool(loop,**kw):
    logging.info('create datebase connection pool')
    global __pool #连接池由全局变量__pool存储
    __pool=await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        # 从字典获取user,password,db等信息
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

loop=asyncio.get_event_loop()
kw={'user':'root','password':'root','db':'testweb'}
loop.run_until_complete(create_pool(loop=loop,**kw))
print(__pool)
#注意：函数使用了关键字参数**kw则传递参数有两种形式
# 第一种形式,传递一个字典，前面需要加**  (**kw)
# 第二种形式，直接以key=value方式传递,key不需要加引号(user='www-data',password='www-data',db='awesome')

async def select(sql):
    log(sql)
    # 通过连接池__pool创建一个 <class 'aiomysql.connection.Connection'>对象conn
    # 前提是运行过协程函数create_pool已经创建了连接池__pool    # 使用这个语句运行会报警告DeprecationWarning,但是可以正常运行
    with await __pool as conn:
    # 使用这个语句不报警告    # async with __pool.acquire() as conn:
        # 使用await conn.cursor(aiomysql.DictCursor)创建一个<class 'aiomysql.cursors.DictCursor'>对象赋值给cur
        cur = await conn.cursor(aiomysql.DictCursor) #建立一个dict类型的游标
        # 执行搜索sql语句为函数传递的sql语句
        await cur.execute(sql)
        # 把所有搜索结果返回，返回为一个list 内部元素为搜索结果对应的0至多个字典
        # 方法cur.fetchmany(size)获取最多指定数量的记录，否则，通过fetchall()获取所有记录
        rs = await cur.fetchall()
        # 关闭
        await cur.close()
        return rs
res=loop.run_until_complete(select('select * from users'))
print(res)

async def execute1(sql,args): #INSERT、UPDATE、DELETE语句，可以定义一个通用的execute()函数
    log(sql)
    with (await __pool) as conn:
        try:
            cur=await conn.cursor()
            await cur.execute(sql.replace('?','%s'),args) #SQL语句的占位符是?，而MySQL的占位符是%s，select()函数在内部自动替换。注意要始终坚持使用带参数的SQL，而不是自己拼接SQL字符串，这样可以防止SQL注入攻击。
            re=cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return re
async def execute(sql,args):
    log(sql)
    with (await __pool) as conn:
        try:
            cur = await conn.cursor()
            await cur.execute(sql.replace('?','%s'),args)
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            logging.info(e)
        finally:
            return affected
res1=loop.run_until_complete(execute1('insert into users values(124,"test2@qq.com","123456789",0,"liuym","http://image",1111111111)',[]))
print(res1)