import React, { Component } from 'react';
import request from 'request';
import { Card, CardBody, CardHeader, Progress } from 'reactstrap';
import 'spinkit/spinkit.css';

class ProgressMonitor extends Component {
  constructor(props) {
    super(props);

    this.state = {
      total_progress: null,
      module_progress: [],
      seconds: 0,
      status: 'Waiting for jobs'
    };
  }

  tick() {
    request({url: `${process.env.REACT_APP_WEBDIS_ADDRESS}/GET/progress_monitor`, json:true},
      function (error, response, body) {
        // console.log(JSON.parse(body['GET']));

      if(body) {
        if(body['GET']){
          let progress_data = JSON.parse(body['GET']);
          this.setState(prevState => ({
            module_progress: progress_data['module_progress'],
            total_progress: progress_data['total_progress'],
            status: progress_data['status']
          }));
        }
      }

    }.bind(this));
    
    this.setState(prevState => ({
      seconds: prevState.seconds + 1,
    }));
  }

  componentDidMount() {
    this.tick();
    this.interval = setInterval(() => this.tick(), 500);
  }

  componentWillUnmount() {
    clearInterval(this.interval);
  }

  render() {
    let module_progress_length = this.state.module_progress.length;

    return (
      <div className="animated fadeIn">
        <Card>
          <CardHeader>
            <i className="cui-align-left progress-group-icon"></i><strong>Experiment Progress</strong>
          </CardHeader>
          <h1>&nbsp;&nbsp;&nbsp;Status: {this.state.status}</h1>
          {module_progress_length === 0 &&
            <div className="sk-fold  sk-center">
                <div className="sk-fold-cube"></div>
                <div className="sk-fold-cube"></div>
                <div className="sk-fold-cube"></div>
                <div className="sk-fold-cube"></div>
            </div>
          }

          {module_progress_length === 0 &&
            <div className="animated fadeIn">
                <h2>&nbsp;&nbsp;&nbsp;</h2>
            </div>
          }

          {this.state.module_progress.map((job, idx) => {
            let num_success_jobs = job['num_complete_jobs'] - job['num_error_jobs'];
            return <CardBody>
              <div className="text-left">{job['module_name']}</div>
              <Progress multi>
                <Progress bar animated color="success" value={num_success_jobs.toString()} max={job['num_total_jobs']}><strong>COMPLETE: {num_success_jobs}</strong></Progress>
                <Progress bar animated value={job['num_running_jobs'].toString()} max={job['num_total_jobs']}><strong>RUNNING: {job['num_running_jobs']}</strong></Progress>
                <Progress bar animated color="warning" value={job['num_ready_jobs'].toString()} max={job['num_total_jobs']}><strong>READY: {job['num_ready_jobs']}</strong></Progress>
                <Progress bar animated color="warning" value={job['num_pending_jobs'].toString()} max={job['num_total_jobs']}><strong>PENDING: {job['num_pending_jobs']}</strong></Progress>
                <Progress bar animated color="danger" value={job['num_error_jobs'].toString()} max={job['num_total_jobs']}><strong>ERROR: {job['num_error_jobs']}</strong></Progress>
              </Progress>
            </CardBody>
            },
          )}
        </Card>
      </div>
    );
  }
}

export default ProgressMonitor;
