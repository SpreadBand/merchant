from billing.integration import Integration
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf.urls.defaults import patterns
from billing.signals import transaction_was_successful, transaction_was_unsuccessful
from django.http import HttpResponse
from billing.models.world_pay_models import WorldPayResponse


RBS_HOSTED_URL_TEST = "https://select-test.wp3.rbsworldpay.com/wcc/purchase"
RBS_HOSTED_URL_LIVE = "https://secure.wp3.rbsworldpay.com/wcc/purchase"

# http://www.rbsworldpay.com/support/bg/index.php?page=development&sub=integration&c=WW

class WorldPayIntegration(Integration):
    # Template for required fields
    fields = {"instId": "",
              "cartId": "",
              "amount": "",
              "currency": "",}

    def __init__(self, options={}):
        super(WorldPayIntegration, self).__init__(options=options)
        if self.test_mode:
            self.fields.update({"testMode": 100})

    def get_urls(self):
        urlpatterns = patterns('',
           (r'^rbs-notify-handler/$', self.notify_handler),
                               )
        return urlpatterns

    @property
    def service_url(self):
        if self.test_mode:
            return RBS_HOSTED_URL_TEST
        return RBS_HOSTED_URL_LIVE

    @csrf_exempt
    @require_POST
    def notify_handler(self, request):
        post_data = request.POST.copy()
        data = {}

        resp_fields = {
            'instId': 'installation_id',
            'compName': 'company_name',
            'cartId': 'cart_id',
            'desc': 'description',
            'amount': 'amount',
            'currency': 'currency',
            'authMode': 'auth_mode',
            'testMode': 'test_mode',
            'transId': 'transaction_id',
            'transStatus': 'transaction_status',
            'transTime': 'transaction_time',
            'authAmount': 'auth_amount',
            'authCurrency': 'auth_currency',
            'authAmountString': 'auth_amount_string',
            'rawAuthMessage': 'raw_auth_message',
            'rawAuthCode': 'raw_auth_code',
            'name': 'name',
            'address': 'address',
            'postcode': 'post_code',
            'country': 'country_code',
            'countryString': 'country',
            'tel': 'phone',
            'fax': 'fax',
            'email': 'email',
            'futurePayId': 'future_pay_id',
            'cardType': 'card_type',
            'ipAddress': 'ip_address',
            }

        for (key, val) in resp_fields.iteritems():
            data[val] = post_data.get(key, '')

        try:
            resp = WorldPayResponse.objects.create(**data)
            # TODO: Make the type more generic
            transaction_was_successful.send(sender=self.__class__, type="purchase", response=resp)
            status = "SUCCESS"
        except:
            transaction_was_unsuccessful.send(sender=self.__class__, type="purchase", response=post_data)
            status = "FAILURE"
        
        return HttpResponse(status)
