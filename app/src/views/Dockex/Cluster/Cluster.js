import React, { Component } from 'react';
import request from "request";

import {Radar} from "react-chartjs-2";
import { Progress, Card, CardBody, CardHeader, Col, Table, CardColumns} from 'reactstrap';

class Cluster extends Component {

  constructor(props) {
    super(props);

    this.state = {
      seconds: 0 ,
      current_cluster_stats: null
    };
  }

  tick() {
    request({url: `${process.env.REACT_APP_WEBDIS_ADDRESS}/GET/cluster_stats`, json:true}, function (error, response, body) {
      if(body) {
        if (body['GET']) {
          this.setState(prevState => ({
            current_cluster_stats: JSON.parse(body['GET'])
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
    this.interval = setInterval(() => this.tick(), 250);
  }

  componentWillUnmount() {
    clearInterval(this.interval);
  }

render() {
    if (this.state.current_cluster_stats) {
      //console.log(typeof this.state.current_cluster_stats);
    return (
        <div className="animated fadeIn">
            <Card>
                <CardHeader>
                    <i className="cui-graph progress-group-icon"></i> <strong>Dockex Cluster</strong>
                    <div className="card-header-actions">
                    </div>
                </CardHeader>
                <CardBody>
                    <div>
                        <Col>
                            <CardColumns className="cols-2">
                                <Card>
                                    <CardBody>
                                        {/*<div className="mw-100 m-0 p-0 chart-wrapper">*/}
                                        <div className="chart-wrapper">
                                            <Col>
                                                <Radar data={{
                                                labels: this.state.current_cluster_stats['cpu_percent_per_cpu'].map((cpu_percent, i) => {
                                                  // return "CPU" + i.toString()
                                                  return ""
                                                }),
                                                datasets: [
                                                  {
                                                    label: 'CPU Utilization',
                                                    // label: '',
                                                    backgroundColor: 'rgba(255,99,132,0.5)',
                                                    borderColor: 'rgba(255,99,132,1)',
                                                    pointBackgroundColor: 'rgba(255,99,132,1)',
                                                    pointBorderColor: '#fff',
                                                    pointHoverBackgroundColor: '#fff',
                                                    pointHoverBorderColor: 'rgba(255,99,132,1)',
                                                    data: this.state.current_cluster_stats['cpu_percent_per_cpu'],
                                                  },
                                                ],
                                                }}
                                                     options={{
                                                       events: [],
                                                       responsive: true,
                                                       maintainAspectRatio: true,
                                                       legend: {
                                                         display: false,
                                                         labels: {
                                                             fontColor: '#fff',
                                                             fontSize: 12,
                                                             fontStyle: 'bold'
                                                         }
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
                                            </Col>
                                        </div>
                                    </CardBody>
                                </Card>
                            <Card>
                                <CardBody>
                                    <Table responsive>
                                      <tbody>
                                        <tr>
                                          <th scope="row">MACHINE COUNT</th>
                                          <td>{this.state.current_cluster_stats['machine_count']}</td>
                                        </tr>
                                        <tr>
                                          <th scope="row">CPU COUNT</th>
                                          <td>{this.state.current_cluster_stats['cpu_count']}</td>
                                        </tr>
                                        <tr>
                                          <th scope="row">RAM (GB)</th>
                                          <td>{Math.floor((this.state.current_cluster_stats['virtual_memory_total'] / 1000000000.0))}</td>
                                        </tr>
                                        <tr>
                                          <th scope="row">GPU COUNT</th>
                                          <td>{this.state.current_cluster_stats['gpu_count']}</td>
                                        </tr>
                                        <tr>
                                          <th scope="row">GPU MEMORY (GB)</th>
                                          <td>{Math.floor((this.state.current_cluster_stats['gpu_memory_total'] / 1000000000.0))}</td>
                                        </tr>
                                        <tr>
                                          <th scope="row"></th>
                                          <td>{null}</td>
                                        </tr>
                                      </tbody>
                                    </Table>

                                    <div className="progress-group">
                                      <div className="progress-group-header">
                                        <i className="fa fa-bandcamp progress-group-icon"></i>
                                        <span className="title">CPU Credits</span>
                                        <span className="ml-auto font-weight-bold"><span
                                          className="text-muted title">{this.state.current_cluster_stats['cpu_credits_used'].toString() + " / " + this.state.current_cluster_stats['cpu_credits_total'].toString()}</span></span>
                                      </div>
                                      <div className="progress-group-bars">
                                        <div>
                                          {/*<span className="ml-auto text-muted small">{"( " + machine['hardware_monitor']['cpu_percent'].toString() + " % )"}</span>*/}
                                          <Progress className="progress-xs" color="info"
                                                    value={((100.0 * this.state.current_cluster_stats['cpu_credits_used'] / this.state.current_cluster_stats['cpu_credits_total'])).toFixed(1).toString()}/>
                                        </div>
                                      </div>
                                    </div>
                                    
                                    <div className="progress-group">
                                      <div className="progress-group-header">
                                        <i className="fa fa-bandcamp progress-group-icon"></i>
                                        <span className="title">GPU Credits</span>
                                        <span className="ml-auto font-weight-bold"><span
                                          className="text-muted title">{this.state.current_cluster_stats['gpu_credits_used'].toString() + " / " + this.state.current_cluster_stats['gpu_credits_total'].toString()}</span></span>
                                      </div>
                                      <div className="progress-group-bars">
                                        <div>
                                          {/*<span className="ml-auto text-muted small">{"( " + machine['hardware_monitor']['gpu_percent'].toString() + " % )"}</span>*/}
                                          <Progress className="progress-xs" color="info"
                                                    value={((100.0 * this.state.current_cluster_stats['gpu_credits_used'] / this.state.current_cluster_stats['gpu_credits_total'])).toFixed(1).toString()}/>
                                        </div>
                                      </div>
                                    </div>

                                    <div className="progress-group">
                                      <div className="progress-group-header">
                                        <i className="fa fa-desktop progress-group-icon"></i>
                                        <span className="title">CPU</span>
                                        <span className="ml-auto font-weight-bold"><span
                                          className="text-muted title">{this.state.current_cluster_stats['cpu_percent'].toString() + " %"}</span></span>
                                       </div>
                                       <div className="progress-group-bars">
                                        <div>
                                          {/*<span className="ml-auto text-muted small">{"( " + this.state.current_cluster_stats['cpu_percent'].toString() + " % )"}</span>*/}
                                          <Progress className="progress-xs" color="red"
                                                    value={this.state.current_cluster_stats['cpu_percent'].toString()}/>
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
                                            className="text-muted title">{this.state.current_cluster_stats['virtual_memory_percent'].toString() + " %"}</span></span>
                                      </div>
                                      <div className="progress-group-bars">
                                        <Progress className="progress-xs" color="blue"
                                                  value={this.state.current_cluster_stats['virtual_memory_percent'].toString()}/>
                                      </div>
                                    </div>

                                    <div className="progress-group">
                                      <div className="progress-group-header">
                                        <i className="fa fa-desktop progress-group-icon"></i>
                                        <span className="title">GPU</span>
                                        <span className="ml-auto font-weight-bold"><span
                                          className="text-muted title">{this.state.current_cluster_stats['gpu_percent'].toString() + " %"}</span></span>
                                      </div>
                                      <div className="progress-group-bars">
                                        <div>
                                          {/*<span className="ml-auto text-muted small">{"( " + this.state.current_cluster_stats['cpu_percent'].toString() + " % )"}</span>*/}
                                          <Progress className="progress-xs" color="green"
                                                    value={this.state.current_cluster_stats['gpu_percent'].toString()}/>
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
                                            className="text-muted title">{this.state.current_cluster_stats['gpu_memory_percent'].toString() + " %"}</span></span>
                                      </div>
                                      <div className="progress-group-bars">
                                        <Progress className="progress-xs" color="warning"
                                                  value={this.state.current_cluster_stats['gpu_memory_percent'].toString()}/>
                                      </div>
                                    </div>

                                </CardBody>
                            </Card>
                        </CardColumns>
                    </Col>
                </div>
            </CardBody>
        </Card>
    </div>
    );
    }
    else {
      return (
      <div className="animated fadeIn">
        <Card>
          <CardHeader>
          </CardHeader>
        </Card>
      </div>
    );
    }
  }
}

export default Cluster;
