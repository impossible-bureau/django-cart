from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class ItemManager(models.Manager):
    def get(self, *args, **kwargs):
        if 'product' in kwargs:
            kwargs['content_type'] = ContentType.objects.get_for_model(type(kwargs['product']))
            kwargs['object_id'] = kwargs['product'].pk
            del(kwargs['product'])
        return super(ItemManager, self).get(*args, **kwargs)


class Item(models.Model):
    cart = models.ForeignKey('Cart', verbose_name=_('cart'))
    quantity = models.PositiveIntegerField(verbose_name=_('quantity'))
    unit_price = models.DecimalField(max_digits=18, decimal_places=2, verbose_name=_('unit price'))
    # product as generic relation
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()

    objects = ItemManager()

    class Meta:
        verbose_name = _('item')
        verbose_name_plural = _('items')
        ordering = ('cart',)

    def __unicode__(self):
        return u'%d units of %s' % (self.quantity, self.product.__class__.__name__)

    def total_price(self):
        return self.quantity * self.unit_price
    total_price = property(total_price)

    # product
    def get_product(self):
        return self.content_type.get_object_for_this_type(pk=self.object_id)

    def set_product(self, product):
        self.content_type = ContentType.objects.get_for_model(type(product))
        self.object_id = product.pk

    product = property(get_product, set_product)


class ProductDoesNotExist(Exception):

    def __init__(self, product):
        self.product = product


class Cart(models.Model):
    creation_date = models.DateTimeField(verbose_name=_('creation date'))
    checked_out = models.BooleanField(default=False, verbose_name=_('checked out'))

    def is_empty(self):
        return self.item_count() == 0

    def empty(self):
        for item in self.items():
            item.delete()

    def items(self):
        return list(self.item_set.all())

    def item_count(self):
        return len(self.items())

    def add_item(self, item, unit_price=0, quantity=1):
        try:
            item = Item.objects.get(cart=self, product=item, unit_price=unit_price)
            item.quantity += quantity
            item.save()
        except Item.DoesNotExist:
            item = Item.objects.create(cart=self, product=item, unit_price=unit_price, quantity=quantity)

    def remove_item(self, item):
        try:
            Item.objects.get(cart=self, product=item).delete()
        except Item.DoesNotExist:
            raise ProductDoesNotExist(item)

    def summary(self):
        return sum(item.total_price for item in self.items())

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')
        ordering = ('-creation_date',)

    def __unicode__(self):
        return unicode(self.creation_date)
