import React, {Component} from 'react';

import dockex_logo from '../../../assets/img/brand/dockex_white.svg'

class Welcome extends Component {
  constructor(props) {
    super(props);

    this.state = {
      fadeIn: true
    };
  }

  render() {

    return (
      <div className="animated fadeIn">
        <img src={dockex_logo} className="img-fluid mx-auto d-block" alt="Welcome" width="1300" height="283" vspace="200"/>
      </div>
    );
  }
}

export default Welcome;
