from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, CreateAPIView

from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from users.models import User, Payment
from users.serializer import UserSerializer, PaymentSerializer
from users.services import create_stripe_product, create_stripe_price, create_stripe_session


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        user.set_password(user.password)
        user.save()

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = (AllowAny,)
        return super().get_permissions()


class PaymentLiatAPIView(ListAPIView):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = (
        "course",
        "lesson",
        "payment_method",
    )
    ordering_fields = ("payment_date",)


class PaymentCreateAPIView(CreateAPIView):
    serializer_class = PaymentSerializer

    def perform_create(self, serializer):
        payment = serializer.save(user=self.request.user)
        product = create_stripe_product(payment)
        if payment.payment_method == "перевод на счет":

            price = create_stripe_price(payment, product)
            session_id, payment_link = create_stripe_session(price)
            payment.session_id = session_id
            payment.link = payment_link
            payment.save()