import React, { Component } from 'react';

class DefaultFooter extends Component {
  render() {
    return (
      <React.Fragment>
        <span><a href="https://github.com/ConnexonSystems/dockex">Dockex</a> &copy; 2019 <a href="http://www.connexonsystems.com">Connexon Systems LLC</a></span>
        <span className="ml-auto"><a href="https://github.com/ConnexonSystems/dockex">Dockex</a> powered by <a href="http://www.connexonsystems.com">Connexon Systems</a></span>
      </React.Fragment>
    );
  }
}

export default DefaultFooter;
