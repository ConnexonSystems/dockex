import React, { Component } from 'react';
import {
  Button,
  Card,
  CardBody,
  CardFooter,
  CardHeader,
  Col,
  Form,
  FormGroup,
  FormText,
  Input,
  Label
} from 'reactstrap';
import request from 'request';
import { Redirect } from 'react-router-dom'


class Launch extends Component {
  constructor(props) {
    super(props);

    this.state = {
      project_path: "",
      experiment: "",
      to_progress: false,
      fadeIn: true
    };

    this.onHandleProjectPathChange = this.onHandleProjectPathChange.bind(this);
    this.onHandleExperimentChange = this.onHandleExperimentChange.bind(this);
    this.onHandleSubmit = this.onHandleSubmit.bind(this);
    this.onHandleReset = this.onHandleReset.bind(this);

    request({url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/GET/app_launcher_project_path`, json:true}, function (error, response, body) {

      // console.log(this.state.local_machine_name);
      // console.log(process.env);
      if(body) {
        if (body['GET']) {
          this.setState(prevState => ({
            project_path: body['GET'].slice(1, -1)
          }));
        }
      }
    }.bind(this));

    request({url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/GET/app_launcher_experiment`, json:true}, function (error, response, body) {

      // console.log(this.state.local_machine_name);
      // console.log(process.env);
      if(body) {
        if (body['GET']) {
          this.setState(prevState => ({
            experiment: body['GET'].slice(1, -1)
          }));
        }
      }
    }.bind(this));

  }

  onHandleProjectPathChange(e) {
    this.setState({
      project_path: e.target.value
    });
  }

  onHandleExperimentChange(e) {
    this.setState({
      experiment: e.target.value
    });
  }

  onHandleSubmit(e) {
    e.preventDefault();

    request({
        url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/RPUSH/redis_launcher`,
        method:'PUT',
        json: {
          "config": {
            "name": this.state.experiment.split("/").join("_"),
            "path": "core/experiment/dockex_experiment",
            "image_tag": "dockex_experiment_image",
            "volumes": {[this.state.project_path]: "/home/experiment/project"},
            "omit_json_pathname_arg": true,
            "bind_mount_docker_socket": true,
            "skip_docker_wrapper_build": true,
            "command_args": this.state.experiment
          }
        }
      }, function (error, response, body) {
      // console.log('error:', error);
      console.log('statusCode:', response && response.statusCode);
      console.log('body:', body);
    });

    request({
        url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/SET/app_launcher_project_path`,
        method:'PUT',
        json: this.state.project_path
      }, function (error, response, body) {
      // console.log('error:', error);
      console.log('statusCode:', response && response.statusCode);
      console.log('body:', body);
    });

    request({
        url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/SET/app_launcher_experiment`,
        method:'PUT',
        json: this.state.experiment
      }, function (error, response, body) {
      // console.log('error:', error);
      console.log('statusCode:', response && response.statusCode);
      console.log('body:', body);
    });

    this.setState(prevState => ({ to_progress: true}));
  }

  onHandleReset(e) {
    e.preventDefault();
    this.setState(prevState => ({ project_path: "", experiment: ""}));
  }

  render() {
    if (this.state.to_progress === true) {
      return <Redirect to='/experiment_progress' />
    }

    return (
      <div className="animated fadeIn">
        <Card>
          <CardHeader>
            <strong>Launch</strong> Experiment
          </CardHeader>
          <CardBody>
            <Form action="" method="post" className="form-horizontal">
              <FormGroup row>
                <Col md="3">
                  <Label>Experiment Path</Label>
                </Col>
                <Col xs="12" md="9">
                    <Input type="text" id="project_path" value={this.state.project_path} name="project_path" placeholder="Enter absolute project path..." autoComplete="project_path" onChange={this.onHandleProjectPathChange}/>
                    <FormText className="help-block">Please enter absolute project path</FormText>
                    <Input type="text" id="experiment" value={this.state.experiment} name="experiment" placeholder="Enter relative experiment path..." autoComplete="experiment" onChange={this.onHandleExperimentChange}/>
                  <FormText className="help-block">Please enter relative experiment path</FormText>
                </Col>
              </FormGroup>
            </Form>
          </CardBody>
          <CardFooter>
            <Button onClick={this.onHandleSubmit} type="submit" size="sm" color="primary"><i className="fa fa-dot-circle-o"></i> Submit</Button>
            <Button onClick={this.onHandleReset} type="reset" size="sm" color="danger"><i className="fa fa-ban"></i> Reset</Button>
          </CardFooter>
        </Card>
      </div>
    );
  }
}

export default Launch;
