from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField, SelectField
from wtforms.widgets import ListWidget, CheckboxInput

class SearchForm(FlaskForm):
    query = StringField('Query', validators=[DataRequired()])
    submit = SubmitField('Search')
    simtype = SelectField('Options', choices=[('tagged', 'Tagged'),
                                              ('auto', 'Auto'),
                                              ('all', 'All')])
