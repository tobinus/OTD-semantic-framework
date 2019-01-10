from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import SubmitField, SelectField
from wtforms.fields.html5 import SearchField
from wtforms.widgets import ListWidget, CheckboxInput
from otd.constants import SIMTYPE_AUTOTAG, SIMTYPE_SIMILARITY, SIMTYPE_ALL

class SearchForm(FlaskForm):
    query = SearchField('Query', validators=[DataRequired()])
    submit = SubmitField('Search')
    simtype = SelectField('Options', choices=[(SIMTYPE_SIMILARITY, 'Tagged'),
                                              (SIMTYPE_AUTOTAG, 'Auto'),
                                              (SIMTYPE_ALL, 'All')])
