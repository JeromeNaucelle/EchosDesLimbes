
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.http.response import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from larp.models import Inscription, Opus
import stripe
import pprint


class HomePageView(TemplateView):
    template_name = 'home.html'


# new
@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)
    

class SuccessView(TemplateView):
    template_name = 'success.html'


class CancelledView(TemplateView):
    template_name = 'cancelled.html'


@csrf_exempt
def create_checkout_session(request, ticket_id: int):
    from larp.models import Ticket

    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'redirect': 1})
        ticket = Ticket.objects.get(pk=ticket_id)

        metadata = {
            "user_id": request.user.pk,
            "access_type": ticket.access_type,
            "opus_id": ticket.opus.pk
        }

        if ticket.access_type != 'PNJV':
            faction_id = int(request.GET['faction'])
            metadata["faction_id"] = faction_id
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            #success_url=domain_url + app_prefix + 'success?session_id={CHECKOUT_SESSION_ID}'
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=request.user.id if request.user.is_authenticated else None,
                success_url = f"{settings.DOMAIN_URL}{reverse('payments:success')}"+'?session_id={CHECKOUT_SESSION_ID}',
                cancel_url = f"{settings.DOMAIN_URL}{reverse('payments:cancelled')}",
                payment_method_types=['card'],
                mode='payment',
                
                line_items = [{
                    'price_data': {
                        'currency': 'eur',
                        'unit_amount': int(ticket.price*100),
                        'product_data': {
                            'name': str(ticket),
                            'description': 'TODO',
                            'metadata': metadata,
                        },
                    },
                    'quantity': 1,
                }
                ],
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})
        
        
@csrf_exempt
def stripe_webhook(request):
    def send_confirmation_mail(user, opus, price):
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string

        context = {
            'user': f"{user.first_name} {user.last_name}",
            'price': price,
            'opus': opus
        }
        text_content = render_to_string(
                "emails/buy_confirmation.txt",
                context=context,
        )

        # Then, create a multipart email instance.
        msg = EmailMultiAlternatives(
            "Les Echos des Limbes : Confirmation de paiement",
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )

        # Lastly, attach the HTML content to the email instance and send.
        #msg.attach_alternative(html_content, "text/html")
        msg.send()


    print("!! stripe_webhook !!")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)


    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        pprint.pprint(event)
        print("Payment was successful.")
        
        # TODO: run some custom code here
        line_items = stripe.checkout.Session.list_line_items(
            event['data']['object']['id'],
            expand=['data.price.product']
            )

        for line in line_items:
            print(f"{line.description} (x1): {float(line.price.unit_amount/100)}")
            user_id = line.price.product.metadata['user_id']
            price = float(line.price.unit_amount/100)
            opus_id = int(line.price.product.metadata['opus_id'])
            opus = Opus.objects.get(pk=opus_id)

            
            infos = {
                'user_id': int(line.price.product.metadata['user_id']),
                'access_type': line.price.product.metadata['access_type'],
                'opus_id': int(line.price.product.metadata['opus_id'])
            }
            if line.price.product.metadata['access_type'] != 'PNJV':
                faction_id = int(line.price.product.metadata['faction_id'])
                infos['faction_id'] = faction_id
            # TODO: check s'il n'existe pas déjà une inscription pour cet utilisateur à cet opus
            Inscription.objects.create(**infos)

            user = User.objects.get(pk=user_id)
            send_confirmation_mail(user, opus, price)

    return HttpResponse(status=200)