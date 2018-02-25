from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from core.products.models import Product
from core.orders.models import Cart, Order, STATUS

User = get_user_model()


class BaseProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['title', 'price', 'option']


class ProductListSerializer(BaseProductSerializer):
    """
    Product model serialization.
    """
    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + ['items', 'id']


class RegisterSerializer(serializers.ModelSerializer):
    """
    User model serialization.
    """
    class Meta:
        model = User
        fields = ('email', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    @staticmethod
    def validate_email(value):
        """check for uniqueness in database"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('The email is taken.')
        return value

    @staticmethod
    def validate_password(value):
        if len(value) < 8:
            raise serializers.ValidationError('Password must be at least 8 letters.')
        return value

    def create(self, validated_data):
        user = self.Meta.model(**validated_data)
        # We won't to store raw passwords,
        # we use user.set_password to hash passwords.
        user.set_password(validated_data['password'])
        user.save()
        return user


class ShowCartsSerializer(serializers.Serializer):
    """
    We want to use the ShowCartsSerializer only for show cart data in api,
    so we won't to create/update Cart objects using it.
    """

    class CartProductSerializer(BaseProductSerializer):
        """
        This object has been used as a part of ShowCartsSerializer.
        """
        selected_item = serializers.CharField()

        class Meta(BaseProductSerializer.Meta):
            fields = BaseProductSerializer.Meta.fields + ['selected_item', 'id']
            read_only_fields = fields  # all fields are read only

    count = serializers.CharField()
    total_price = serializers.CharField()
    products = CartProductSerializer(many=True)

    class Meta:
        fields = ('count', 'total_price', 'products')
        read_only_fields = '__all__'

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CartSerializer(serializers.ModelSerializer):
    """
    core.carts.models.Cart model serialization.
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Cart
        fields = ('product', 'user', 'customization')

    def validate(self, attrs):
        cart = self.Meta.model(**attrs)
        # Apply custom model's level validations.
        try:
            cart.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return attrs


class OrderListSerializer(serializers.ModelSerializer):
    """
    We will use it for create/retrieve order objects.
    """
    status = serializers.SerializerMethodField(source='status')
    date = serializers.DateTimeField(format='%d %b %Y-%H:%M', required=False)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Order
        fields = ('id', 'status', 'date', 'location', 'user', 'total_price')
        read_only_fields = ('id', 'status', 'date', 'total_price')

    @staticmethod
    def get_status(obj):
        if isinstance(obj, Order):
            return obj.status_label
        try:
            return STATUS.get(obj['status'], obj['status'])
        except KeyError:
            return None

    def validate(self, attrs):
        if not Cart.objects.filter(user=attrs.get('user')).exists():
            raise serializers.ValidationError("Cart is empty.")
        return attrs
