from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField

class TagForm(FlaskForm):
    ontologyRef = StringField('Ontology UUID', validators=[DataRequired()])
    dcatDataset = StringField('DCAT Dataset', validators=[DataRequired()])
    submit = SubmitField('Tag')

