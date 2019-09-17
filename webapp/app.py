import os

import nltk
from flask import (Flask, render_template, request, send_from_directory, jsonify)
from werkzeug import secure_filename

import app_constants
import lk_parser
import resumeDB_pb2
import search
import upload_resume
from lk_parser import findResumeByURL

SECTION_SEPERATOR = " \r\n"
app = Flask(__name__)


app.config['UPLOAD_FOLDER'] = './Resumes/'

def uploadFile(file):
    Filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], Filename))
    return Filename

@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/classifier')
def pageClassifier():
    return render_template('classify.html')


@app.route('/searcher')
def searcher():
    return render_template('search.html')


@app.route('/uploader')
def uploader():
    return render_template('upload.html')


@app.route('/creator')
def creator():
    return render_template('create.html')


@app.route('/createResumeAction', methods=['POST'])
def createResumeAction():
    # print(request.form)

    nameRaw = request.form['name']
    profileURL = request.form['profileURL']
    role = request.form['role']
    monthlySalary = request.form['monthlySalary']
    aboutRaw = request.form['about']
    experienceRaw = request.form['experience']
    educationRaw = request.form['education']
    licensesCertificationsRaw = request.form['licensesCertifications']
    skillsEndorsementsRaw = request.form['skillsEndorsements']

    # pickle.dump(experienceRaw, open('experience.pickle', "wb"))
    # pickle.dump(educationRaw, open('education.pickle', "wb"))

    # rawResume can be searched by KNN like pdf, docx formats.
    # pdf, docx text should be saved into rawResume.
    rawResume = nameRaw + SECTION_SEPERATOR + role + SECTION_SEPERATOR + "monthlysalary: " \
                + monthlySalary + SECTION_SEPERATOR + aboutRaw + SECTION_SEPERATOR + \
                experienceRaw + SECTION_SEPERATOR + licensesCertificationsRaw + SECTION_SEPERATOR + \
                skillsEndorsementsRaw

    try:
        uploadfile = request.files['uploadfile']
    except:
        uploadfile = None

    if uploadfile:
        result = uploadFile(uploadfile)
        URL = result
    else:
        URL = profileURL

    result = upload_resume.insertResume(nameRaw, URL, rawResume)

    # For protobuf DB.
    db = lk_parser.loadData(app_constants.RESUMEDB_FILE_PB)
    resume = findResumeByURL(db, profileURL)
    if resume is None:
        resume = resumeDB_pb2.Resume()

    resume.name = nameRaw
    resume.profileURL = profileURL
    resume.rawResume = rawResume
    resume.monthlySalary = float(monthlySalary)

    if role.find(' at ') != -1:
        resume.companyName = role.split(" at ")[1]
        resume.title = role.split(" at ")[0]

    resume.aboutRaw = aboutRaw
    resume.educationRaw = educationRaw
    resume.educations.extend(lk_parser.extractEducations(educationRaw))
    resume.experienceRaw = experienceRaw
    resume.experiences.extend(lk_parser.extractExperiences(experienceRaw))
    resume.licensesCertificationsRaw = licensesCertificationsRaw
    resume.skillsEndorsementsRaw = skillsEndorsementsRaw

    resumeExists = findResumeByURL(db, profileURL)
    if resumeExists is None:
        db.resumes.append(resume)

    lk_parser.saveData(app_constants.RESUMEDB_FILE_PB, db)

    return "{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}".format(nameRaw,profileURL,role,monthlySalary,aboutRaw,
                                                                     experienceRaw,educationRaw,
                                                                     licensesCertificationsRaw,skillsEndorsementsRaw)

@app.route('/searchResumeAction', methods=['POST', 'GET'])
def searchResumeAction():
    searchImportantKey = request.form['importantKey']
    algorithm_type = request.form['algorithmType']
    try:
        searchImportantKey = request.form['importantKey']
    except:
        searchImportantKey = None

    searchOptionKey = request.form['optionKey']

    if searchImportantKey:

        if "KNN" == algorithm_type:
            result = search.res(searchImportantKey, searchOptionKey)
        elif "cosinesim" == algorithm_type:
            result = search.ui_search(searchImportantKey)

        hasA = search.gethasA()
        hasB = search.gethasB()
        print(result)
        return str(result)
        #return render_template('searchResumePageResult.html', results=result, hasA=hasA, hasB=hasB)
    else:
        result = "No 'Mandatory Search Key' input"
        return render_template('searchResumePageResult.html', results=result)

    return "Searching with {0} and {1} and {2}".format(searchImportantKey, searchOptionKey, algorithm_type)


@app.route('/resumeSubmit', methods=['GET', 'POST'])
def get_resume():
    # data = json.dumps(request.form)
    print(request.form)
    return "Classifying"


if __name__ == '__main__':
    app.run()