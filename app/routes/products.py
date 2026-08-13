from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
import pytz
from app import db
from app.models import Product, Category, StorageLocation, History

bp = Blueprint('products', __name__, url_prefix='/products')

@bp.route('/')
@login_required
def list_products():
    filter_status = request.args.get('status', 'todos')
    category_id = request.args.get('category', type=int)
    search = request.args.get('q', '').strip()

    query = Product.query.filter_by(user_id=current_user.id, active=True)

    if category_id:
        query = query.filter_by(category_id=category_id)

    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.brand.ilike(f'%{search}%'),
                Product.barcode.ilike(f'%{search}%')
            )
        )

    products = query.all()
    tz = pytz.timezone('America/Sao_Paulo')
    today = datetime.now(tz).date()

    # Ordenação inteligente
    def sort_key(p):
        if p.no_expiration or not p.expiration_date:
            return (5, datetime.max.date())
        days = (p.expiration_date - today).days
        if days < 0:
            return (0, p.expiration_date)
        elif days == 0:
            return (1, p.expiration_date)
        elif days <= 3:
            return (2, p.expiration_date)
        elif days <= 7:
            return (3, p.expiration_date)
        elif days <= 30:
            return (4, p.expiration_date)
        else:
            return (5, p.expiration_date)

    products.sort(key=sort_key)

    if filter_status != 'todos':
        products = [p for p in products if p.get_status() == filter_status]

    categories = Category.query.filter(
        (Category.user_id == current_user.id) | (Category.user_id == None)
    ).all()
    locations = StorageLocation.query.filter_by(user_id=current_user.id).all()

    return render_template('products.html', 
        products=products, 
        categories=categories,
        locations=locations,
        filter_status=filter_status,
        search=search
    )

@bp.route('/new', methods=['GET', 'POST'])
@bp.route('/new/<barcode>', methods=['GET', 'POST'])
@login_required
def new_product(barcode=None):
    tz = pytz.timezone('America/Sao_Paulo')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('O nome do produto é obrigatório.', 'warning')
            return redirect(request.referrer or url_for('products.new_product'))

        barcode_input = request.form.get('barcode', '').strip()
        brand = request.form.get('brand', '').strip()
        category_id = request.form.get('category_id', type=int)
        quantity = request.form.get('quantity', '1')
        unit = request.form.get('unit', 'unidade')
        expiration_str = request.form.get('expiration_date', '').strip()
        no_expiration = request.form.get('no_expiration') == 'on'
        location_id = request.form.get('location_id', type=int)
        notes = request.form.get('notes', '').strip()

        try:
            quantity = float(quantity.replace(',', '.'))
        except:
            quantity = 1

        expiration_date = None
        if not no_expiration and expiration_str:
            try:
                expiration_date = datetime.strptime(expiration_str, '%d/%m/%Y').date()
                today = datetime.now(tz).date()
                if expiration_date < today:
                    if request.form.get('confirm_past') != '1':
                        flash('A data de validade já passou. Confirme para cadastrar.', 'warning')
                        return redirect(request.referrer or url_for('products.new_product'))
            except ValueError:
                flash('Data de validade inválida. Use o formato DD/MM/AAAA.', 'warning')
                return redirect(request.referrer or url_for('products.new_product'))

        product = Product(
            user_id=current_user.id,
            barcode=barcode_input or None,
            name=name,
            brand=brand or None,
            category_id=category_id,
            quantity=quantity,
            unit=unit,
            expiration_date=expiration_date,
            no_expiration=no_expiration,
            storage_location_id=location_id,
            notes=notes or None,
        )
        db.session.add(product)
        db.session.commit()

        # Registrar histórico
        history = History(
            user_id=current_user.id,
            product_id=product.id,
            product_name=product.name,
            action='cadastrado',
            quantity_change=quantity,
            notes=f'Produto cadastrado com {quantity} {unit}'
        )
        db.session.add(history)
        db.session.commit()

        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard.index'))

    # Verificar se código já existe
    existing = None
    if barcode:
        existing = Product.query.filter_by(user_id=current_user.id, barcode=barcode).first()

    categories = Category.query.filter(
        (Category.user_id == current_user.id) | (Category.user_id == None)
    ).all()
    locations = StorageLocation.query.filter_by(user_id=current_user.id).all()

    return render_template('product_form.html', 
        barcode=barcode, 
        existing=existing,
        categories=categories,
        locations=locations,
        product=None
    )

@bp.route('/<int:id>')
@login_required
def detail(id):
    product = Product.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    history = History.query.filter_by(product_id=id, user_id=current_user.id).order_by(History.created_at.desc()).all()
    return render_template('product_detail.html', product=product, history=history)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    product = Product.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.brand = request.form.get('brand', '').strip() or None
        product.category_id = request.form.get('category_id', type=int)
        product.barcode = request.form.get('barcode', '').strip() or None

        try:
            product.quantity = float(request.form.get('quantity', '1').replace(',', '.'))
        except:
            pass

        product.unit = request.form.get('unit', 'unidade')

        expiration_str = request.form.get('expiration_date', '').strip()
        product.no_expiration = request.form.get('no_expiration') == 'on'

        if not product.no_expiration and expiration_str:
            try:
                product.expiration_date = datetime.strptime(expiration_str, '%d/%m/%Y').date()
            except ValueError:
                flash('Data de validade inválida.', 'warning')
                return redirect(url_for('products.edit', id=id))
        else:
            product.expiration_date = None

        product.storage_location_id = request.form.get('location_id', type=int)
        product.notes = request.form.get('notes', '').strip() or None
        product.updated_at = datetime.now(pytz.timezone('America/Sao_Paulo'))

        db.session.commit()

        history = History(
            user_id=current_user.id,
            product_id=product.id,
            product_name=product.name,
            action='editado',
            notes='Produto editado'
        )
        db.session.add(history)
        db.session.commit()

        flash('Produto atualizado!', 'success')
        return redirect(url_for('products.detail', id=id))

    categories = Category.query.filter(
        (Category.user_id == current_user.id) | (Category.user_id == None)
    ).all()
    locations = StorageLocation.query.filter_by(user_id=current_user.id).all()

    return render_template('product_form.html', 
        product=product,
        categories=categories,
        locations=locations,
        barcode=product.barcode,
        existing=None
    )

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    product = Product.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    product.active = False
    db.session.commit()

    history = History(
        user_id=current_user.id,
        product_id=product.id,
        product_name=product.name,
        action='excluido',
        notes='Produto excluído'
    )
    db.session.add(history)
    db.session.commit()

    flash('Produto removido.', 'info')
    return redirect(url_for('dashboard.index'))

@bp.route('/<int:id>/consume', methods=['POST'])
@login_required
def consume(id):
    product = Product.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    try:
        amount = float(request.form.get('amount', '1').replace(',', '.'))
    except:
        amount = 1

    if product.quantity > 0:
        product.quantity = max(0, product.quantity - amount)
        db.session.commit()

        history = History(
            user_id=current_user.id,
            product_id=product.id,
            product_name=product.name,
            action='consumido',
            quantity_change=-amount,
            notes=f'Consumido {amount} {product.unit}'
        )
        db.session.add(history)
        db.session.commit()

        flash(f'Consumido {amount} {product.unit} de {product.name}', 'success')
    else:
        flash('Quantidade já está em zero.', 'warning')

    return redirect(request.referrer or url_for('dashboard.index'))

@bp.route('/<int:id>/add-stock', methods=['POST'])
@login_required
def add_stock(id):
    product = Product.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    try:
        amount = float(request.form.get('amount', '1').replace(',', '.'))
    except:
        amount = 1

    product.quantity += amount
    db.session.commit()

    history = History(
        user_id=current_user.id,
        product_id=product.id,
        product_name=product.name,
        action='estoque_adicionado',
        quantity_change=amount,
        notes=f'Adicionado {amount} {product.unit} ao estoque'
    )
    db.session.add(history)
    db.session.commit()

    flash(f'Adicionado {amount} {product.unit} ao estoque de {product.name}', 'success')
    return redirect(request.referrer or url_for('dashboard.index'))
