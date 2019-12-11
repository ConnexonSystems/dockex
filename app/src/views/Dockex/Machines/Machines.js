import React, { Component } from 'react';
import request from "request";

import { Progress } from 'reactstrap';
import {Radar} from "react-chartjs-2";
import { Button, Card, CardBody, CardHeader, Input, Collapse, Row, Col, Table, Form } from 'reactstrap';

class Machines extends Component {

  constructor(props) {
    super(props);
    this.toggleAccordion = this.toggleAccordion.bind(this);
    this.onHandleCreditsChange = this.onHandleCreditsChange.bind(this);
    this.onHandleSubmit = this.onHandleSubmit.bind(this);

    this.state = {
      machine_list: [],
      local_machine_name: null,
      accordion: [],
      status: 'Closed',
      credits_update: 0,
      timeout: 300,
    };
  }

  onHandleCreditsChange(e) {
    this.setState({
      credits_update: parseInt(e.target.value, 10)
    });
  }

  onHandleSubmit(e, redis_address, type) {
    request({url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/RPUSH/credits_updater`, method:'PUT', json: {"redis_address": redis_address, "type": type, "mode": 'set', "value": this.state.credits_update}}, function (error, response, body) {
      // console.log('error:', error); // Print the error if one occurred
      console.log('statusCode:', response && response.statusCode); // Print the response status code if a response was received
      console.log('body:', body); // Print the HTML for the Google homepage.
    });
  }

  toggleAccordion(idx) {

    const state = this.state.accordion;
    state[idx] = !state[idx];

    this.setState({
      accordion: state,
    });
  }

  tick() {
    request({url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/LRANGE/cluster_monitor/0/-1`, json:true}, function (error, response, body) {
      console.log(body);
      // console.log(process.env);
      if(body) {
        if (body['LRANGE']) {
          let machine_data = body['LRANGE'];

          let num_machines = machine_data.length;
          let previous_accordion = this.state.accordion;

          if(num_machines > previous_accordion.length) {
            for (var i = previous_accordion.length; i < num_machines; ++i) {
              previous_accordion.push(true);
            }
          }

          if(machine_data[0]) {
           this.setState(prevState => ({
            machine_list: machine_data.map(s => JSON.parse(s)),
            accordion: previous_accordion
            }));
          }
        }
      }
    }.bind(this));

    request({url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/GET/machine_name`, json:true}, function (error, response, body) {

      // console.log(this.state.local_machine_name);
      // console.log(process.env);
      if(body) {
        if (body['GET']) {
          this.setState(prevState => ({
            local_machine_name: body['GET']
          }));
        }
      }
    }.bind(this));
  }

  componentDidMount() {
    this.tick();
    this.interval = setInterval(() => this.tick(), 500);
  }

  componentWillUnmount() {
    clearInterval(this.interval);
  }

  render() {
    return (
      <div className="animated fadeIn">
        <Card>
          <CardHeader>
            <i className="fa fa-cubes progress-group-icon"></i> Machines
            <div className="card-header-actions">
            </div>
          </CardHeader>
          <CardBody>
            <div id="accordion">
              {this.state.machine_list.map((machine, idx) => {
                console.log(machine);
                return <div>
                  <Col>
                    <Card>
                      <CardHeader id={"heading_" + machine['machine_name']}>
                        <Button block color="link" className="text-left m-0 p-0" onClick={() => this.toggleAccordion(idx)} aria-expanded={this.state.accordion[idx]} aria-controls={"collapse_" + machine['machine_name']}>
                          <h5 className="m-0 p-0"> {machine['machine_name']}</h5>
                        </Button>
                      </CardHeader>
                      <Collapse isOpen={this.state.accordion[idx]} data-parent="#accordion" id={"collapse_" + machine['machine_name']} aria-labelledby={"heading_" + machine['machine_name']}>
                        <CardBody>
                          <Row>
                            <Col xl="6">
                              <div className="animated fadeIn">
                                <Card>
                                  <CardBody>
                                    {/*<div className="mw-100 m-0 p-0 chart-wrapper">*/}
                                    <div className="chart-wrapper">
                                      <Row>
                                      <Radar data={{
                                        labels: machine['hardware_monitor']['cpu_percent_per_cpu'].map((cpu_percent, i) => {
                                          // return "CPU" + i.toString()
                                          return ""
                                        }),
                                        datasets: [
                                          {
                                            // label: 'CPU Utilization',
                                            label: '',
                                            backgroundColor: 'rgba(255,99,132,0.2)',
                                            borderColor: 'rgba(255,99,132,1)',
                                            pointBackgroundColor: 'rgba(255,99,132,1)',
                                            pointBorderColor: '#fff',
                                            pointHoverBackgroundColor: '#fff',
                                            pointHoverBorderColor: 'rgba(255,99,132,1)',
                                            data: machine['hardware_monitor']['cpu_percent_per_cpu'],
                                          },
                                        ],
                                      }}
                                             options={{
                                               events: [],
                                               responsive: true,
                                               maintainAspectRatio: false,
                                               legend: {
                                                 display: false
                                               },
                                               scale: {
                                                 ticks: {
                                                   beginAtZero: true,
                                                   max: 100,
                                                   display: false,
                                                 },
                                                 gridLines: {
                                                   color: 'rgba(255,255,255,1)',
                                                   lineWidth: 2
                                                 },
                                               }
                                             }}/>
                                      </Row>

                                    <div className="progress-group">
                                      <div className="progress-group-header">
                                        <i className="fa fa-bandcamp progress-group-icon"></i>
                                        <span className="title">CPU Credits</span>
                                        <span className="ml-auto font-weight-bold"><span
                                          className="text-muted title">{machine['credits_monitor']['cpu_credits_used'].toString() + " / " + machine['credits_monitor']['cpu_credits_total'].toString()}</span></span>
                                      </div>
                                      <div className="progress-group-bars">
                                        <div>
                                          {/*<span className="ml-auto text-muted small">{"( " + machine['hardware_monitor']['cpu_percent'].toString() + " % )"}</span>*/}
                                          <Progress className="progress-xs" color="info"
                                                    value={(100.0 * machine['credits_monitor']['cpu_credits_used'] / machine['credits_monitor']['cpu_credits_total']).toFixed(1).toString()}/>
                                        </div>
                                      </div>
                                    </div>
                                      
                                    <div className="progress-group">
                                      <div className="progress-group-header">
                                        <i className="fa fa-bandcamp progress-group-icon"></i>
                                        <span className="title">GPU Credits</span>
                                        <span className="ml-auto font-weight-bold"><span
                                          className="text-muted title">{machine['credits_monitor']['gpu_credits_used'].toString() + " / " + machine['credits_monitor']['gpu_credits_total'].toString()}</span></span>
                                      </div>
                                      <div className="progress-group-bars">
                                        <div>
                                          {/*<span className="ml-auto text-muted small">{"( " + machine['hardware_monitor']['gpu_percent'].toString() + " % )"}</span>*/}
                                          <Progress className="progress-xs" color="info"
                                                    value={(100.0 * machine['credits_monitor']['gpu_credits_used'] / machine['credits_monitor']['gpu_credits_total']).toFixed(1).toString()}/>
                                        </div>
                                      </div>
                                    </div>

                                    <div className="progress-group">
                                      <div className="progress-group-header">
                                        <i className="fa fa-desktop progress-group-icon"></i>
                                        <span className="title">CPU</span>
                                        <span className="ml-auto font-weight-bold"><span
                                          className="text-muted title">{machine['hardware_monitor']['cpu_percent'].toString() + " %"}</span></span>
                                      </div>
                                      <div className="progress-group-bars">
                                        <div>
                                          {/*<span className="ml-auto text-muted small">{"( " + machine['hardware_monitor']['cpu_percent'].toString() + " % )"}</span>*/}
                                          <Progress className="progress-xs" color="red"
                                                    value={machine['hardware_monitor']['cpu_percent'].toString()}/>
                                        </div>
                                      </div>
                                    </div>

                                    <div className="progress-group">
                                      <div className="progress-group-header">
                                        <i className="fa fa-floppy-o progress-group-icon"></i>
                                        <span className="title">RAM</span>
                                        <span
                                          className="ml-auto font-weight-bold">
                                          <span
                                            className="text-muted title">{machine['hardware_monitor']['virtual_memory_percent'].toString() + " %"}</span></span>
                                      </div>
                                      <div className="progress-group-bars">
                                        <Progress className="progress-xs" color="blue"
                                                  value={machine['hardware_monitor']['virtual_memory_percent'].toString()}/>
                                      </div>
                                    </div>

                                    <div className="progress-group">
                                      <div className="progress-group-header">
                                        <i className="fa fa-desktop progress-group-icon"></i>
                                        <span className="title">GPU</span>
                                        <span className="ml-auto font-weight-bold"><span
                                          className="text-muted title">{machine['hardware_monitor']['gpu_percent'].toString() + " %"}</span></span>
                                      </div>
                                      <div className="progress-group-bars">
                                        <div>
                                          {/*<span className="ml-auto text-muted small">{"( " + machine['hardware_monitor']['cpu_percent'].toString() + " % )"}</span>*/}
                                          <Progress className="progress-xs" color="green"
                                                    value={machine['hardware_monitor']['gpu_percent'].toString()}/>
                                        </div>
                                      </div>
                                    </div>

                                    <div className="progress-group">
                                      <div className="progress-group-header">
                                        <i className="fa fa-floppy-o progress-group-icon"></i>
                                        <span className="title">GPU Memory</span>
                                        <span
                                          className="ml-auto font-weight-bold">
                                          <span
                                            className="text-muted title">{machine['hardware_monitor']['gpu_memory_percent'].toString() + " %"}</span></span>
                                      </div>
                                      <div className="progress-group-bars">
                                        <Progress className="progress-xs" color="warning"
                                                  value={machine['hardware_monitor']['gpu_memory_percent'].toString()}/>
                                      </div>
                                    </div>

                                  </div>
                                  </CardBody>
                                </Card>
                              </div>
                            </Col>
                            <Col xl="6">
                              <div className="animated fadeIn">
                                <Card>
                                  <CardBody>
                                    <Table responsive>
                                      <tbody>
                                        <tr>
                                          <th scope="row">CPU CREDITS TOTAL</th>
                                          <td>
                                            {machine['credits_monitor']['cpu_credits_total']}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                            <Button outline color="primary" onClick={() => {
                                              request({url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/RPUSH/credits_updater`, method:'PUT', json: {"redis_address": machine['redis_address'], "type": "cpu", "mode": 'decr'}}, function (error, response, body) {
                                              }.bind(this));
                                            }}>
                                              {/*<span className="cui-arrow-left"></span> Log Table*/}
                                              <span className="fa fa-chevron-left"></span>
                                            </Button>
                                            <Button outline color="primary" onClick={() => {
                                              request({url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/RPUSH/credits_updater`, method:'PUT', json: {"redis_address": machine['redis_address'], "type": "cpu", "mode": 'incr'}}, function (error, response, body) {
                                              }.bind(this));
                                            }}>
                                              {/*<span className="cui-arrow-left"></span> Log Table*/}
                                              <span className="fa fa-chevron-right"></span>
                                            </Button>
                                            <br />
                                            <br />
                                              <Form action="" method="put" className="form-inline">
                                              <Input type="text" id={idx.toString()} name={idx.toString()} placeholder="Update" autoComplete={idx.toString()} onChange={this.onHandleCreditsChange}/>&nbsp;&nbsp;&nbsp;
                                              <Button onClick={(e) => this.onHandleSubmit(e, machine['redis_address'], "cpu")} size="sm" color="primary"><i className="fa fa-dot-circle-o"></i> Update</Button>
                                              </Form>
                                          </td>
                                        </tr>

                                        <tr>
                                          <th scope="row">GPU CREDITS TOTAL</th>
                                          <td>
                                            {machine['credits_monitor']['gpu_credits_total']}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                            <Button outline color="primary" onClick={() => {
                                              request({url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/RPUSH/credits_updater`, method:'PUT', json: {"redis_address": machine['redis_address'], "type": "gpu", "mode": 'decr'}}, function (error, response, body) {
                                              }.bind(this));
                                            }}>
                                              {/*<span className="cui-arrow-left"></span> Log Table*/}
                                              <span className="fa fa-chevron-left"></span>
                                            </Button>
                                            <Button outline color="primary" onClick={() => {
                                              request({url:`${process.env.REACT_APP_WEBDIS_ADDRESS}/RPUSH/credits_updater`, method:'PUT', json: {"redis_address": machine['redis_address'], "type": "gpu", "mode": 'incr'}}, function (error, response, body) {
                                              }.bind(this));
                                            }}>
                                              {/*<span className="cui-arrow-left"></span> Log Table*/}
                                              <span className="fa fa-chevron-right"></span>
                                            </Button>
                                            <br />
                                            <br />
                                              <Form action="" method="put" className="form-inline">
                                              <Input type="text" id={idx.toString()} name={idx.toString()} placeholder="Update" autoComplete={idx.toString()} onChange={this.onHandleCreditsChange}/>&nbsp;&nbsp;&nbsp;
                                              <Button onClick={(e) => this.onHandleSubmit(e, machine['redis_address'], "gpu")} size="sm" color="primary"><i className="fa fa-dot-circle-o"></i> Update</Button>
                                              </Form>
                                          </td>
                                        </tr>
                                        <tr>
                                          <th scope="row">STATUS</th>
                                          <td>{machine['status']}</td>
                                        </tr>
                                        <tr>
                                          <th scope="row">CPU CREDITS USED</th>
                                          <td>{machine['credits_monitor']['cpu_credits_used']}</td>
                                        </tr>
                                        <tr>
                                          <th scope="row">GPU CREDITS USED</th>
                                          <td>{machine['credits_monitor']['gpu_credits_used']}</td>
                                        </tr>
                                        <tr>
                                          <th scope="row">WEBDIS ADDRESS</th>
                                          <td>{machine['webdis_address']}</td>
                                        </tr>
                                        <tr>
                                          <th scope="row">REDIS ADDRESS</th>
                                          <td>{machine['redis_address']}</td>
                                        </tr>
                                        <tr>
                                          <th scope="row">DATA PATH</th>
                                          <td>{machine['data_path']}</td>
                                        </tr>
                                      </tbody>
                                    </Table>
                                  </CardBody>
                                </Card>
                              </div>
                            </Col>
                          </Row>
                        </CardBody>
                      </Collapse>
                    </Card>
                  </Col>
                </div>
                }
              )}
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }
}

export default Machines;
