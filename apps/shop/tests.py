from django.test import TestCase, Client
from apps.accounts.models import User
from apps.catalog.models import Category, Product, ProductVariant
from apps.orders.models import ServiceablePin, Order
from apps.orders.services import change_status
class Flow(TestCase):
    def test_flow(self):
        c=Client()
        cat=Category.objects.create(name="C",slug="c"); p=Product.objects.create(category=cat,name="P",slug="p")
        v=ProductVariant.objects.create(product=p,label="1 kg",sku="S1",price=100,stock=10)
        ServiceablePin.objects.create(pincode="712601")
        self.assertEqual(c.get("/").status_code,200)
        r=c.post("/register/",{"name":"Ram","phone":"9876543210","password":"Strong#Pass99"}); self.assertEqual(r.status_code,302)
        c.post("/cart/add/",{"variant_id":v.pk,"qty":2})
        self.assertEqual(c.get("/cart/").status_code,200)
        self.assertEqual(c.get("/checkout/").status_code,302)
        r=c.post("/addresses/new/?next=/checkout/",{"full_name":"Ram","phone":"9876543210","line1":"x","village_town":"V","district":"Hooghly","pincode":"712601"}); self.assertEqual(r.status_code,302)
        r=c.get("/checkout/"); self.assertEqual(r.status_code,200)
        a=User.objects.get().addresses.get()
        r=c.post("/checkout/",{"address":a.pk,"payment_method":"UPI","token":"abc"}); self.assertEqual(r.status_code,302,r.content[:500])
        o=Order.objects.get(); self.assertEqual(c.get(f"/orders/{o.order_no}/").status_code,200)
        self.assertEqual(c.get(f"/orders/{o.order_no}/invoice/").status_code,302)
        c.post(f"/orders/{o.order_no}/pay/",{"reference":"123456789012"})
        change_status(o,"CONFIRMED")
        r=c.get(f"/orders/{o.order_no}/invoice/"); self.assertEqual(r.status_code,200); self.assertContains(r,"TAX INVOICE")
        self.assertEqual(c.get("/orders/").status_code,200); self.assertEqual(c.get("/addresses/").status_code,200)
        c.post("/logout/"); r=c.post("/login/",{"username":"98765 43210","password":"Strong#Pass99"}); self.assertEqual(r.status_code,302)


class PagesRender(TestCase):
    def test_public_pages(self):
        c = Client()
        for url in ["/", "/login/", "/register/", "/cart/"]:
            self.assertEqual(c.get(url).status_code, 200, url)
        cat = Category.objects.create(name="C", slug="c")
        Product.objects.create(category=cat, name="Nirmala", slug="nirmala-agri-vita-green-gold")
        ProductVariant.objects.create(product=Product.objects.get(), label="1 kg", sku="N1", price=100, stock=5)
        self.assertContains(c.get("/"), "nirmala-agri-vita-green-gold-1.webp")


class Language(TestCase):
    def test_default_bengali_and_switch(self):
        c = Client(HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9")  # phone set to English: still Bengali by default
        r = c.get("/")
        self.assertContains(r, "দোকান")
        self.assertContains(r, 'lang="bn"')
        r = c.post("/i18n/setlang/", {"language": "en", "next": "/"})
        self.assertEqual(r.status_code, 302)
        r = c.get("/")  # cookie remembered
        self.assertContains(r, "Our Products")
        self.assertContains(r, "বাংলা")  # button to switch back
        self.assertEqual(c.get("/admin/login/").status_code, 200)


class BengaliCartBar(TestCase):
    def test_cart_bar_in_bengali(self):
        c = Client()
        cat = Category.objects.create(name="C", slug="c")
        p = Product.objects.create(category=cat, name="P", name_bn="পণ্য-ক", slug="p")
        v = ProductVariant.objects.create(product=p, label="1 kg", sku="B1", price=100, stock=5)
        c.post("/cart/add/", {"variant_id": v.pk, "qty": 2})
        r = c.get("/")
        self.assertContains(r, "টি পণ্য")
        self.assertContains(r, "পণ্য-ক")  # Bengali product name
        self.assertContains(r, "কার্টে নিন")
