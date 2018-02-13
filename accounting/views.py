from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import SignupForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import SignupForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import django_excel as excel
from .models import Accounting
from django.shortcuts import render_to_response
from datetime import datetime
from django.views.generic import (TemplateView,ListView,
                                  DetailView,CreateView,
                                  UpdateView,DeleteView)

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
import pandas as pd
import pyexcel as pe
from django.http import HttpResponse
from django import forms
from django.db.models import Sum
import datetime
import numpy as np
from decimal import Decimal
import decimal, simplejson
import json
from django_pandas.io import read_frame

import matplotlib.pyplot as plt
import pandas as pd
from pandas.tools.plotting import table

import datetime as dt


def home(request):
    return render(request, 'accounting/home.html')


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            message = render_to_string('acc_active_email.html', {
                'user':user, 'domain':current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            # Sending activation link in terminal
            # user.email_user(subject, message)
            mail_subject = 'Activate your blog account.'
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            return render(request, 'accounting/acc_active_sent.html')
            #return HttpResponse('Please confirm your email address to complete the registration.')
            # return render(request, 'acc_active_sent.html')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, 'accounting/thankyou.html')
    else:
        return HttpResponse('Activation link is invalid!')

class UploadFileForm(forms.Form):
    file = forms.FileField()

class DecimalJSONEncoder(simplejson.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalJSONEncoder, self).default(o)

@login_required
def handson_table_accounting(request):
    return excel.make_response_from_tables(
    [Accounting], 'handsontable.html')



@login_required
def import_Accounting(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST,
                              request.FILES)
        def choice_func(row):
            q = Question.objects.filter(slug=row[0])[0]
            row[0] = q
            return row
        if form.is_valid():
            request.FILES['file'].save_book_to_database(
                models=[Accounting],
                initializers=[None, choice_func],
                mapdicts=[
                    ['company','history', 'date', 'debit','credit','amount','conta_devedora','conta_credora']]
            )
            return render(request, 'accounting/thankyou2.html')
        else:
            return HttpResponseBadRequest()
    else:
        form = UploadFileForm()
    return render(
        request,
        'upload_form.html',
            {
            'form': form,
            'title': 'Import excel data into database',
            'header': "Please upload your accounting Journal:"
        })


@login_required
def Statements_Upload_Accounting(request):
    #df = Accounting.objects.filter(date__year=2018)
    df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    #qs = Accounting.objects.all()
    #df = read_frame(qs)
    table_2016_credito = pd.pivot_table(df, values='amount',columns=['credit'], aggfunc=np.sum)
    table_2016_debito = pd.pivot_table(df, values='amount',columns=['debit'], aggfunc=np.sum)
    table_2016_debito = pd.concat([table_2016_debito,pd.DataFrame(columns=table_2016_credito.columns)])
    table_2016_credito = pd.concat([table_2016_credito,pd.DataFrame(columns=table_2016_debito.columns)])
    table_2016_credito = table_2016_credito.fillna(0)
    table_2016_debito = table_2016_debito.fillna(0)
    balance = table_2016_debito - table_2016_credito
    cash = balance['Banco Itau'][-1]
    faturamento = balance['Faturamento'][-1]
    taxes = balance['Others'][-1]
    qs = Accounting.pdobjects.all()
    #df2 = qs.to_dataframe()

    #response = df2.to_html('accounting/templates/accounting/edu.html')
    #response2 = balance.to_html('accounting/templates/accounting/balance.html')


    #image_data = open("accounting/templates/accounting/mytable.png", "rb").read()
    #return HttpResponse(image_data, content_type="image/png")
    #return render(request,'accounting/edu.html')
    #return render(request,'accounting/balance.html')

    #teste = df.between_time(dt(2018,1,1) ,dt(2018-1-31))
    #df2 = pd.DataFrame(list(Accounting.objects.all().values('history', 'date', 'amount')))
    #df3 = pd.DataFrame(list(Accounting.objects.aggregate(Sum('amount'))))
    #df4 = df['amount'].sum()
    return render_to_response('accounting/name.html', context={'faturamento':faturamento,'cash':cash, "taxes":taxes})

def download(request):
    context = {

        'submit_btn': "excel"
        }
    return render(request, 'download.html',context)

def excel_download(request):
    qs = Accounting.pdobjects.all()
    df2 = qs.to_dataframe()
    fsock = df2.to_excel('accounting/templates/accounting/razao.xlsx',engine='openpyxl', index=False)
    fsock = open('accounting/templates/accounting/razao.xlsx', 'rb')
    response = HttpResponse(fsock, content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="report.xls"'
    return response


@login_required
def General_Ledger(request):
    qs = Accounting.pdobjects.filter(date__year=2018).values()
    df2 = qs.to_dataframe()
    return render_to_response('accounting/ledger.html',{'data':df2.to_html(index=False,columns=['date','history','debit','credit','amount'])})


@login_required
def Balance_Sheet(request):
    df = pd.DataFrame(list(Accounting.pdobjects.all().values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    table_credito = pd.pivot_table(df, values='amount',columns=['credit'], aggfunc=np.sum)
    table_debito = pd.pivot_table(df, values='amount',columns=['debit'], aggfunc=np.sum)
    table_debito = pd.concat([table_debito,pd.DataFrame(columns=table_credito.columns)])
    table_credito = pd.concat([table_credito,pd.DataFrame(columns=table_debito.columns)])
    table_credito = table_credito.fillna(0)
    table_debito = table_debito.fillna(0)
    balance = table_debito - table_credito
    itau = '{:,}'.format(balance['Banco Itau'][-1])
    bradesco = '{:,}'.format(balance['Banco Bradesco'][-1])
    ISS = '{:,}'.format(balance['ISS a Compensar'][-1])
    Adto_Fornecedores = '{:,}'.format(balance['Adto a Fornecedores'][-1])
    SOCIOS = '{:,}'.format(balance['Adto a Socios'][-1])
    current_assets = '{:,}'.format(balance['Banco Itau'][-1] + balance['ISS a Compensar'][-1]+balance['Banco Bradesco'][-1]+balance['Adto a Fornecedores'][-1]+balance['Adto a Socios'][-1])
    RD = '{:,}'.format(balance['R&D'][-1])
    depreciation = '{:,}'.format(balance['Depr. Acumulada'][-1])
    total_other_assets = '{:,}'.format(balance['R&D'][-1] + balance['Depr. Acumulada'][-1])
    total_assets = '{:,}'.format(balance['Banco Itau'][-1] + balance['ISS a Compensar'][-1]+balance['Banco Bradesco'][-1]+balance['Adto a Fornecedores'][-1]
                    +balance['Adto a Socios'][-1]+balance['R&D'][-1]+balance['Depr. Acumulada'][-1])
    TAXES = '{:,}'.format(-balance['TAXES'][-1])
    LOAN = '{:,}'.format(-balance['Emprestimos Socios'][-1])
    SUPPLIERS = '{:,}'.format(-balance['Fornecedores a Pagar'][-1])
    CLOUDROUTE = '{:,}'.format(-balance['Cloudroute'][-1])
    current_liabilities = '{:,}'.format(-(balance['TAXES'][-1] + balance['Fornecedores a Pagar'][-1] + balance['Cloudroute'][-1] + balance['Income_Taxes'][-1]))
    CAPITAL = '{:,}'.format(-(balance['Capital Subscrito'][-1] + balance['Capital a Integralizar'][-1]))
    RESULTADOS = '{:,}'.format(-(balance['Reserva de Capital'][-1] + balance['Ajuste de Exercicios Anteriores'][-1] + balance['Lucros Distribuidos'][-1]+ balance['Lucro Acumuado'][-1]))
    REVENUE = balance['REVENUE'][-1]
    Income_Taxes = '{:,}'.format(-balance['Income_Taxes'][-1])
    # INCOME_TAX = '{:,}'.format(-balance['INCOME_TAX'][-1])
    GA = balance['G&A'][-1]
    SGA = balance['SG&A'][-1]
    CMV = balance['CMV'][-1]
    MGMT = balance['MGMT'][-1]
    TARIFA = balance['Desp Bancarias'][-1]
    JUROS = balance['Receitas Financeiras'][-1]
    LUCRO = (-(balance['REVENUE'][-1] + balance['G&A'][-1] + balance['SG&A'][-1] + balance['CMV'][-1] + balance['MGMT'][-1] + balance['Desp Bancarias'][-1] + balance['Receitas Financeiras'][-1]
                +balance['Amortizacao'][-1]+balance['INCOME_TAX'][-1]))
    #taxes = balance['Impostos a Recolher'][-1]
    total_liabilities = '{:,}'.format(-(balance['TAXES'][-1] + balance['Income_Taxes'][-1]+ balance['Emprestimos Socios'][-1] + balance['Fornecedores a Pagar'][-1] + balance['Cloudroute'][-1] + balance['Capital Subscrito'][-1] +
                            balance['Capital a Integralizar'][-1] + balance['Reserva de Capital'][-1]+ balance['Ajuste de Exercicios Anteriores'][-1] + balance['Lucros Distribuidos'][-1]+ balance['Lucro Acumuado'][-1]- LUCRO))
    EQUITY = '{:,}'.format(-(balance['Capital Subscrito'][-1] + balance['Capital a Integralizar'][-1] + balance['REVENUE'][-1] + balance['G&A'][-1] + balance['SG&A'][-1] + balance['CMV'][-1] + balance['MGMT'][-1] +
                balance['Desp Bancarias'][-1] + balance['Receitas Financeiras'][-1]+
                balance['Reserva de Capital'][-1] + balance['Ajuste de Exercicios Anteriores'][-1] + balance['Lucros Distribuidos'][-1]+ balance['Lucro Acumuado'][-1]))
    #pl = balance['PL'][-1]
    #total_liabilities = taxes + pl
    period = '2018'
    #current_ratio = "{0:.2f}%".format(total_assets / -taxes)
    #working_capital = '{0:,}'.format(total_assets + taxes)
    return render_to_response('accounting/index.html', context={'period':period,'itau':itau,'bradesco':bradesco,'ISS':ISS,'SOCIOS': SOCIOS,'Adto_Fornecedores':Adto_Fornecedores,'total_assets':total_assets,
    						 'Income_Taxes':Income_Taxes, 'GA':GA, 'SGA':SGA, 'RD': RD,'CMV':CMV, 'TAXES':TAXES, 'REVENUE':REVENUE,'MGMT':MGMT,'TARIFA':TARIFA, 'current_assets':current_assets,
                                'depreciation':depreciation,'LOAN':LOAN,'CLOUDROUTE':CLOUDROUTE,'SUPPLIERS':SUPPLIERS,
                                "current_liabilities": current_liabilities,"CAPITAL":CAPITAL,'RESULTADOS': RESULTADOS,
                                'JUROS':JUROS, 'LUCRO':LUCRO, 'total_liabilities': total_liabilities, 'EQUITY':EQUITY,
                                'total_other_assets':total_other_assets})





@login_required
def Income_Statement(request):

    df = pd.DataFrame(list(Accounting.objects.filter(date__year=2018).values()))
    table_2016_credito = pd.pivot_table(df, values='amount',columns=['credit'], aggfunc=np.sum)
    table_2016_debito = pd.pivot_table(df, values='amount',columns=['debit'], aggfunc=np.sum)
    table_2016_debito = pd.concat([table_2016_debito,pd.DataFrame(columns=table_2016_credito.columns)])
    table_2016_credito = pd.concat([table_2016_credito,pd.DataFrame(columns=table_2016_debito.columns)])
    table_2016_credito = table_2016_credito.fillna(0)
    table_2016_debito = table_2016_debito.fillna(0)
    balance = table_2016_debito - table_2016_credito
    faturamento = '{:,.2f}'.format(-balance['REVENUE'][-1])
    cogs = '{:,.2f}'.format(-balance['CMV'][-1])
    gross_profit = '{:,.2f}'.format(-(balance['REVENUE'][-1]+balance['CMV'][-1]))
    gross_profit2 = (-(balance['REVENUE'][-1]+balance['CMV'][-1]))
    general = '{:,.2f}'.format(-balance['G&A'][-1])
    SGA = '{:,.2f}'.format(-balance['SG&A'][-1])
    MGMT = '{:,.2f}'.format(-balance['MGMT'][-1])
    AMORTIZACAO = '{:,.2f}'.format(-balance['Amortizacao'][-1])
    FINANCE = '{:,.2f}'.format(-balance['Desp Bancarias'][-1] - balance['Receitas Financeiras'][-1])
    ttl_expenses = '{:,.2f}'.format(-balance['G&A'][-1] - balance['SG&A'][-1] - balance['MGMT'][-1] - balance['Amortizacao'][-1] - balance['Desp Bancarias'][-1] - balance['Receitas Financeiras'][-1])
    ttl_expenses2 = (-balance['G&A'][-1] - balance['SG&A'][-1] - balance['MGMT'][-1] - balance['Amortizacao'][-1] - balance['Desp Bancarias'][-1] - balance['Receitas Financeiras'][-1])
    BC = gross_profit2 + ttl_expenses2

    if BC >= 20000:
        Income_Tax = '{:,.2f}'.format(-(float(BC) * 0.15) - ((float(BC) -20000)*0.10) - (float(BC) * 0.09))
        Income_Tax2 = (-(float(BC) * 0.15) - ((float(BC) -20000)*0.10) - (float(BC) * 0.09))
    elif BC <= 20000:
        Income_Tax = '{:,.2f}'.format(-(float(BC) * 0.15) - (float(BC) * 0.09))
        Income_Tax2 = (-(float(BC) * 0.15) - (float(BC) * 0.09))
    elif BC <0:
        Income_Tax = 'R$ 0.00'
        Income_Tax2 = 0

    net_expenses = '{:,.2f}'.format(float(BC) + Income_Tax2)
    return render_to_response('accounting/dre.html', context={'faturamento':faturamento, "net_income":faturamento,"cogs":cogs, "gross_profit":gross_profit, 'general':general, "SGA":SGA,"MGMT":MGMT, "AMORTIZACAO":AMORTIZACAO, "FINANCE": FINANCE, 'ttl_expenses': ttl_expenses, "Income_Tax":Income_Tax, "net_expenses": net_expenses })




def bs_itau(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    Itau = df[(df.debit == 'Banco Itau') | (df.credit == 'Banco Itau')]
    return render_to_response('accounting/Itau.html',{"xls":Itau.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_bradesco(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    Bradesco = df[(df.debit == 'Banco Bradesco') | (df.credit == 'Banco Bradesco')]
    return render_to_response('accounting/Bradesco.html',{"xls":Bradesco.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_socios(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    socios = df[(df.debit == 'Adto a Socios') | (df.credit == 'Adto a Socios')]
    return render_to_response('accounting/socios.html',{"xls":socios.to_html(index=False,columns=['date','history','debit','credit','amount'])})



def bs_fornecedores(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    fornecedores = df[(df.debit == 'Adto a Fornecedores') | (df.credit == 'Adto a Fornecedores')]
    return render_to_response('accounting/fornecedores.html',{"xls":fornecedores.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_RD(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    RD = df[(df.debit == 'R&D') | (df.credit == 'R&D')]
    return render_to_response('accounting/R&D.html',{"xls":RD.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_depreciation(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    depreciation = df[(df.debit == 'Depr. Acumulada') | (df.credit == 'Depr. Acumulada')]
    return render_to_response('accounting/depreciation.html',{"xls":depreciation.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_retidos(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    retidos = df[(df.debit == 'TAXES') | (df.credit == 'TAXES')]
    return render_to_response('accounting/retidos.html',{"xls":retidos.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_payable(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    payable = df[(df.debit == 'Fornecedores a Pagar') | (df.credit == 'Fornecedores a Pagar')]
    return render_to_response('accounting/payable.html',{"xls":payable.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_Income_Tax(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    Income_Tax = df[(df.debit == 'Income_Taxes') | (df.credit == 'Income_Taxes')]
    return render_to_response('accounting/Income_Tax.html',{"xls":Income_Tax.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_Sales(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    Sales = df[(df.debit == 'REVENUE') | (df.credit == 'REVENUE')]
    return render_to_response('accounting/Revenue.html',{"xls":Sales.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_CMV(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    CMV = df[(df.debit == 'CMV') | (df.credit == 'CMV')]
    return render_to_response('accounting/COGS.html',{"xls":CMV.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_GA(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    GA = df[(df.debit == 'G&A') | (df.credit == 'G&A')]
    return render_to_response('accounting/G&A.html',{"xls":GA.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_SGA(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    SGA = df[(df.debit == 'SG&A') | (df.credit == 'SG&A')]
    return render_to_response('accounting/SG&A.html',{"xls":SGA.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_MGMT(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    MGMT = df[(df.debit == 'MGMT') | (df.credit == 'MGMT')]
    return render_to_response('accounting/MGMT.html',{"xls":MGMT.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_AMORTIZATION(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    AMORTIZATION = df[(df.debit == 'Amortizacao') | (df.credit == 'Amortizacao')]
    return render_to_response('accounting/AMORTIZATION.html',{"xls":AMORTIZATION.to_html(index=False,columns=['date','history','debit','credit','amount'])})

def bs_FINANCE(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    FINANCE = df[(df.debit == 'Desp Bancarias') | (df.credit == 'Desp Bancarias') | (df.credit == 'Receitas Financeiras') | (df.debit == 'Receitas Financeiras')]
    return render_to_response('accounting/FINANCE.html',{"xls":FINANCE.to_html(index=False,columns=['date','history','debit','credit','amount'])})


def bs_INCOME(request):
    df = pd.DataFrame(list(Accounting.pdobjects.filter(date__year=2018).values()))
    #df = pd.DataFrame(list(Accounting.objects.filter(date__year=2017).values()))
    INCOME = df[(df.debit == 'INCOME_TAX') | (df.credit == 'INCOME_TAX')]
    return render_to_response('accounting/INCOME.html',{"xls":INCOME.to_html(index=False,columns=['date','history','debit','credit','amount'])})
