from django.db import models

# Create your models here.

# 用户表
class User(models.Model):
    # TODO: 在migration后，手动添加设置初始值的SQL代码 alter sequence user_id restart with 100000
    user_id = models.BigAutoField(primary_key = True)

    name = models.CharField(max_length = 40)
    nickname = models.CharField(max_length = 40)
    password = models.CharField(max_length = 32)
    regist_time = models.DateTimeField()
    email = models.EmailField(null = True, blank = True)
    description = models.CharField(max_length = 100, null = True, blank = True)

    image_height = models.PositiveIntegerField(null=True, blank=True, editable=False, default="100")
    image_width = models.PositiveIntegerField(null=True, blank=True, editable=False, default="100")
    avatar = models.ImageField(upload_to = 'Img/avatar/', width_field = image_width, height_field = image_height, null = True, blank = True)

    class Meta:
        db_table = 'User'

# 分类表
class Category(models.Model):
    cate_id = models.BigAutoField(primary_key = True)

    cate_name = models.CharField(max_length = 40)

    class Meta:
        db_table = 'Category'

# 博客内容表
class Blog(models.Model):
    blog_id = models.BigAutoField(primary_key = True)

    user = models.ForeignKey(User, on_delete = models.CASCADE )
    cate = models.ForeignKey(Category, on_delete = models.CASCADE )
    content = models.TextField()
    title = models.CharField(max_length = 100)
    view_num = models.IntegerField()
    like_num = models.IntegerField()
    create_time = models.DateTimeField()
    modified_time = models.DateTimeField()

    class Meta:
        db_table = 'Blog'

# 评论表
class Comment(models.Model):
    comment_id = models.BigAutoField(primary_key = True)

    blog = models.ForeignKey(Blog, on_delete = models.CASCADE )
    user = models.ForeignKey(User, on_delete = models.CASCADE )
    content = models.CharField(max_length = 600)
    time = models.DateTimeField()

    class Meta:
        db_table = 'Comment'

# 标签表
class Tag(models.Model):
    tag_id = models.BigAutoField(primary_key = True)

    tag_name = models.CharField(max_length = 40)

    class Meta:
        db_table = 'Tag'

# 博客-标签表
class BlogTag(models.Model):
    blog_tag_id = models.BigAutoField(primary_key = True)

    blog = models.ForeignKey(Blog, on_delete = models.CASCADE )
    tag = models.ForeignKey(Tag, on_delete = models.CASCADE )

    class Meta:
        db_table = 'BlogTag'

# 管理员表
class Admin(models.Model):
    # TODO: 在migration后，手动添加设置初始值的SQL代码 alter sequence admin_id restart with 10000
    admin_id = models.BigAutoField(primary_key = True)

    password = models.CharField(max_length = 32)

    class Meta:
        db_table = 'Admin'

# 收藏夹表
class Favourite(models.Model):
    favourite_id = models.BigAutoField(primary_key = True)

    user = models.ForeignKey(User, on_delete = models.CASCADE )
    blog = models.ForeignKey(Blog, on_delete = models.CASCADE )

    class Meta:
        db_table = 'Favourite'

# 关注表
class Follow(models.Model):
    follow_id = models.BigAutoField(primary_key = True)

    # 由于两个外键都指向了User，所以需要设置related_name
    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'follows' )
    fld_user = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'followers' )

    class Meta:
        db_table = 'Follow'

# 通知表
class Notification(models.Model):
    noti_id = models.BigAutoField(primary_key = True)

    user = models.ForeignKey(User, on_delete = models.CASCADE )
    content = models.CharField(max_length = 400)
    unread = models.BooleanField(default = True)

    class Meta:
        db_table = 'Notification'

# Cookie表
class Cookie(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE )
    cookie = models.CharField(max_length = 20)

    class Meta:
        db_table = 'Cookie'
