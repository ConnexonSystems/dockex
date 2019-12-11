import React, { Component } from 'react';
import { AppAsideToggler, AppNavbarBrand, AppSidebarToggler } from '@coreui/react';
import dockex_logo from '../../assets/img/brand/dockex_white.svg'

class DefaultHeader extends Component {
  render() {
    return (
      <React.Fragment>
        <AppSidebarToggler className="d-lg-none" display="md" mobile />
        <AppNavbarBrand
          full={{ src: dockex_logo, width: 120, alt: 'Dockex Logo' }}
          minimized={{ src: dockex_logo, width: 120, alt: 'Dockex Logo' }}
        />
        <AppSidebarToggler className="mr-auto d-md-down-none" display="lg" />
        <AppAsideToggler className="d-md-down-none" />
      </React.Fragment>
    );
  }
}

export default DefaultHeader;
