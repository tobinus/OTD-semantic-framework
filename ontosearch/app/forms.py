from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField, SelectField
from wtforms.widgets import ListWidget, CheckboxInput
from otd.constants import SIMTYPE_AUTOTAG, SIMTYPE_SIMILARITY, SIMTYPE_ALL

class SearchForm(FlaskForm):
    query = StringField('Query', validators=[DataRequired()])
    submit = SubmitField('Search')
    simtype = SelectField('Options', choices=[(SIMTYPE_SIMILARITY, 'Tagged'),
                                              (SIMTYPE_AUTOTAG, 'Auto'),
                                              (SIMTYPE_ALL, 'All')])
