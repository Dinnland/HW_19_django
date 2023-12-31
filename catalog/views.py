from django.contrib.auth.decorators import permission_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.forms import inlineformset_factory
from django.http import request, Http404
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views import generic
from pytils.translit import slugify
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from django.contrib.auth.models import User, Group
from catalog.forms import *
from catalog.models import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from catalog.services import *
# Create your views here. контроллеры


def redirect_view(request):
    """перенаправляет урл сразу на /home/"""
    response = redirect('/home/')
    return response


def base(request):
    """ Базовый шаблон с меню, футером и тд """
    context = {'title': 'Dinnland'}
    return render(request, 'catalog/base.html', context)


def index_contacts(request):
    """Стр с контактами"""
    context = {
        'header': 'Контакты'
               }
    return render(request, 'catalog/contacts.html', context)


# @permission_required('')
class ProductListView(LoginRequiredMixin,  ListView):
    """Главная стр с продуктами"""
    model = Product
    template_name = 'catalog/home.html'

    # ограничение доступа анонимных пользователей
    # 19 Уведомление для неавторизованных пользователей
    login_url = 'catalog:not_authenticated'
    # PermissionRequiredMixin,
    # permission_required = 'catalog.'

    # def get_queryset(self):
    #     """показывает продукты, которые созданы владельцем-юзером"""
    #     return super().get_queryset().filter(owner=self.request.user)


class ProductDetailView(LoginRequiredMixin, DetailView):
    """ стр с продуктом"""
    model = Product
    template_name = 'catalog/product_detail.html'

    def get_context_data(self, **kwargs):
        """КЭШирование для вывода версий"""
        context_data = super().get_context_data(**kwargs)
        context_data['versions'] = get_cashed_versions_for_product(self.object.pk)
        return context_data


class ProductCreateView(LoginRequiredMixin, CreateView):
    """страница для создания продукта"""
    model = Product
    form_class = ProductCreateForm
    success_url = reverse_lazy('catalog:home')

    # ограничение доступа анонимных пользователей
    # 19 Уведомление для неавторизованных пользователей
    login_url = 'catalog:not_authenticated'

    permission_classes = (IsAuthenticated,)

    def form_valid(self, form):
        self.object = form.save()
        self.object.owner = self.request.user
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['category_list'] = get_cashed_categories_for_product()
        return context_data


class ProductUpdateView(LoginRequiredMixin, SuccessMessageMixin, PermissionRequiredMixin, UpdateView):
    """страница для Изменения продукта"""
    model = Product
    # gr = request.user.groups.values_list('name', flat=False)

    def get_form_class(self, queryset=None):
        """Тут в зависимости от группы юзера выводятся разные формы продукта"""
        self.object = super().get_object(queryset)
        # if self.object.owner == self.request.user:
        # if self.request.user.groups.filter(name='moderator').exists():
        #     form_class = ProductUpdateFormModerator
        #     return form_class
        # else:
        #     form_class = ProductUpdateForm
        #     return form_class
        form_class = get_filter_user_group(del_group='moderator', user=self.request.user)
        return form_class

    def get_object(self, queryset=None):
        """проверка: владелец ли хочет редактнуть объект"""
        self.object = super().get_object(queryset)
        if self.request.user.groups.filter(name='moderator').exists():
            return self.object
        else:
            if self.object.owner != self.request.user:
                # return  redirect(reverse('catalog:no_rights'))
                raise Http404
            else:
                return self.object

    # ограничение доступа анонимных пользователей # 19 Уведомление для неавторизованных пользователе
    login_url = 'catalog:not_authenticated'
    permission_required = 'catalog.change_product'

    # # Уведомление об обновлении продукта
    # login_url = 'catalog:update_product'
    success_message = 'Материал был успешно обновлен'

    def get_success_url(self):
        return reverse('catalog:update_product', args=[self.kwargs.get('pk')])

    def get_context_data(self,  queryset=None, **kwargs):
        context_data = super().get_context_data(**kwargs)
        self.object = super().get_object(queryset)

        # # Тут ТУПО убираем для 'moderator' версии продукта из видимости
        # if not self.request.user.groups.filter(name='moderator').exists():
        #     # context_data = super().get_context_data(**kwargs)
        #     version_formset = inlineformset_factory(Product, Version, form=VersionForm, extra=1)
        #     if self.request.method == 'POST':
        #         context_data['formset'] = version_formset(self.request.POST, instance=self.object)
        #         # return context_data
        #     else:
        #         context_data['formset'] = version_formset(instance=self.object)
        #         # return context_data
        # return context_data

        return get_del_group_for_versions(self_req=self.request, del_user='moderator', context_data=context_data, self=self)

    def form_valid(self, form):

        formset = self.get_context_data()['formset']
        self.object = form.save()
        if formset.is_valid():
            formset.instance = self.object
            formset.save()

        return super().form_valid(form)


class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """страница для удаления Product"""
    model = Product
    # fields = ('__all__')
    # fields = ('header', 'content', 'image')
    success_url = reverse_lazy('catalog:home')

    # ограничение доступа анонимных пользователей # 19 Уведомление для неавторизованных пользователей
    login_url = 'catalog:not_authenticated'
    permission_required = 'catalog.delete_product'
    success_message = 'Материал был успешно Удален'

# Блог
class BlogCreateView(CreateView):
    """страница для создания блога"""
    model = Blog
    # fields = ('__all__')
    fields = ('header', "slug", 'content', 'image', 'date_of_create')
    success_url = reverse_lazy('catalog:listblog')

    def form_valid(self, form):
        """динамическое формирование Slug"""
        if form.is_valid():
            new_blog = form.save()
            new_blog.slug = slugify(new_blog.header)
            new_blog.save()
        return super().form_valid(form)


class BlogListView(ListView):
    """ Главная стр с блогами"""
    model = Blog

    def get_queryset(self, queryset=None, *args, **kwargs):
        """Метод для вывода ТОЛЬКО опубликованных блогов"""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = queryset.filter(sign_of_publication=True)

        # item = get_object_or_404(Blog, pk=some_pk)
        # items_table = item.name_table__set.all()
        # image_items = item.name_images_table__set.all()
        return queryset


class BlogDetailView(DetailView):
    """Стр с блогом"""
    model = Blog

    def get_object(self, queryset=None):
        """Метод для подсчета просмотров"""
        self.object = super().get_object(queryset)
        self.object.quantity_of_views += 1
        self.object.save()
        return self.object

    def get_success_url(self):
        return reverse('catalog:viewblog', args=[self.kwargs.get('pk')])


class BlogUpdateView(UpdateView):
    """страница для Изменения блога"""
    model = Blog
    # fields = ('__all__')
    fields = ('header', 'content', 'image')
    # success_url = reverse_lazy('catalog:listblog')

    def form_valid(self, form):
        """динамическое формирование Slug"""
        if form.is_valid():
            new_blog = form.save()
            new_blog.slug = slugify(new_blog.header)
            new_blog.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('catalog:viewblog')


class BlogDeleteView(DeleteView):
    """страница для удаления блога"""
    model = Blog
    # fields = ('__all__')
    # fields = ('header', 'content', 'image')
    success_url = reverse_lazy('catalog:listblog')


class NotAuthenticated(ListView):
    """not_authenticated"""
    model = Product
    template_name = 'catalog/not_authenticated.html'


class NoRights(ListView):
    """NoRights"""
    model = Product
    template_name = 'catalog/no_rights.html'

